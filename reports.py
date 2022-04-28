from typing import List, Union

import matplotlib.pyplot as plt
from solana.rpc.api import Client

from models import AccountTransaction, BlockStakeCommitment, Block, Transaction
from utils import JSONable, Report
from utils.constants import *
from utils.plot import plot_bars
from tqdm import tqdm


class BlockCommitmentReport(Report):
    def __init__(
        self,
        metadata: JSONable,
        results: dict,
    ):
        super(BlockCommitmentReport, self).__init__(metadata)
        self.results = results

    @classmethod
    def capture(
        cls,
        metadata: Union[JSONable, List[JSONable], dict],
        api_client: Client,
        blocks_slots: List[int],
    ):
        results = {}
        for slot in blocks_slots:
            response = api_client.get_block_commitment(slot)[RESULT]
            if response[COMMITMENT] is None:
                return None

            results[slot] = BlockStakeCommitment(
                response[COMMITMENT], response[TOTAL_STAKE]
            )

        return cls(metadata, results)

    def _plot_one(self, ax, slot):
        block_stake_commitment: BlockStakeCommitment = self.results[slot]
        votes = block_stake_commitment.stake_votes
        total_stake = block_stake_commitment.total_epoch_active_stake
        plot_bars(
            ax,
            dict(reversed([(i + 1, vote) for i, vote in enumerate(votes)])),
            color="blue",
            move=0,
        )
        ax.hlines(
            [total_stake, 2 / 3 * total_stake],
            -1,
            33,
            colors=["red"],
            label="epoch active stake",
        )
        ax.hlines(
            [2 / 3 * total_stake],
            -1,
            33,
            colors=["orange"],
            label="super majority",
        )
        ax.set_xlabel("slots behind")
        ax.set_ylabel("stake voted on lockout")
        ax.set_title(f"Lockout stake voted on block {slot}")
        ax.legend()

    def plot(self, slot=None):
        if slot is None:
            slots = list(self.results.keys())
            _, axes = plt.subplots(1, len(slots), figsize=(10, 5 * len(slots)))
            if len(slots) > 1:
                for i, slot in enumerate(slots):
                    self._plot_one(axes[i], slot)
            else:
                self._plot_one(axes, slots[0])
        else:
            _, ax = plt.subplots(1, 1, figsize=(10, 5))
            self._plot_one(ax, slot)

        plt.show()


class BlocksReport(Report):
    def __init__(self, metadata, results):
        self.metadata = metadata
        self.results = results

    @classmethod
    def parse_block(cls, block_json, slot, commitment):
        return (
            Block(
                slot=slot,
                commitment=commitment,
                blockhash=block_json[BLOCKHASH],
                previous_blockhash=block_json[PREVIOUS_BLOCKHASH],
                parent_slot=block_json[PARENT_SLOT],
                block_time=block_json[BLOCK_TIME],
                block_height=block_json[BLOCK_HEIGHT],
                rewards=block_json[REWARDS],
            ),
            block_json[TRANSACTIONS],
        )

    @classmethod
    def parse_transaction(cls, transaction_json):
        transaction = Transaction(
            signatures=transaction_json[TRANSACTION][SIGNATURES],
            err=transaction_json[META],
            fee=transaction_json[META][FEE],
            rewards=transaction_json[META][REWARDS],
            transaction_instructions=transaction_json[TRANSACTION][MESSAGE][
                INSTRUCTIONS
            ],
        )
        transaction.transaction_accounts = cls.parse_transaction_accounts(
            transaction_json, transaction._id
        )
        return transaction

    @classmethod
    def parse_transaction_accounts(cls, transaction_json, transaction_id):
        account_keys = transaction_json[TRANSACTION][MESSAGE][ACCOUNT_KEYS]
        pre_balances = transaction_json[META][PRE_BALANCES]
        posts_balances = transaction_json[META][POST_BALANCES]
        num_readonly_signed_accounts = transaction_json[TRANSACTION][MESSAGE][HEADER][
            NUM_READONLY_SIGNED_ACCOUNTS
        ]
        num_readonly_unsigned_accounts = transaction_json[TRANSACTION][MESSAGE][HEADER][
            NUM_READONLY_UNSIGNED_ACCOUNTS
        ]
        num_required_signatures = transaction_json[TRANSACTION][MESSAGE][HEADER][
            NUM_REQUIRED_SIGNATURES
        ]
        readonly = [
            num_required_signatures - num_readonly_signed_accounts
            < i
            < num_required_signatures
            or i > len(account_keys) - num_readonly_unsigned_accounts
            for i in range(len(account_keys))
        ]
        signed = [i < num_required_signatures for i in range(len(account_keys))]
        signatures = transaction_json[TRANSACTION][SIGNATURES] + [None] * (
            len(account_keys) - num_required_signatures
        )
        return [
            AccountTransaction(
                transaction_id=transaction_id,
                pubkey=pubkey,
                pre_balance=pre_balance,
                post_balance=post_balance,
                read_only=is_readonly,
                signed=is_signed,
                signature=signature,
            )
            for pubkey, pre_balance, post_balance, is_readonly, is_signed, signature in zip(
                account_keys, pre_balances, posts_balances, readonly, signed, signatures
            )
        ]

    @classmethod
    def capture(
        cls,
        metadata: Union[JSONable, List[JSONable], dict],
        api_client: Client,
        blocks_slots: List[int],
    ):
        blocks = {}
        transactions = {}
        transactions_accounts = {}

        for slot in blocks_slots:
            print("Processing block", slot)

            block_json = api_client.get_block(slot)[RESULT]
            block, block_transactions = cls.parse_block(block_json, slot, FINALIZED)

            for transaction_json in tqdm(block_transactions):
                transaction = cls.parse_transaction(transaction_json)

                transactions[transaction._id] = transaction
                block.transactions.append(transaction)

            blocks[block._id] = block

        return cls(
            metadata,
            {
                "blocks": blocks,
                "transactions": transactions,
                "transactions_accounts": transactions_accounts,
            },
        )
