import json
import time
from pathlib import Path
from typing import List

from solana.rpc.api import Client
from tqdm import tqdm

from models import AccountTransaction, Block, InstructionTransaction, Transaction
from utils.constants import *


def parse_block(block_json, slot, commitment):
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
            transactions=[],
            signatures=[],
        ),
        block_json[TRANSACTIONS],
    )


def parse_transaction(transaction_json, slot):
    transaction = Transaction(
        block=slot,
        signatures=transaction_json[TRANSACTION][SIGNATURES],
        err=transaction_json[META][ERR],
        fee=transaction_json[META][FEE],
        rewards=transaction_json[META][REWARDS],
        transaction_instructions=transaction_json[TRANSACTION][MESSAGE][INSTRUCTIONS],
    )
    transaction.transaction_accounts = parse_transaction_accounts(
        transaction_json, transaction._id
    )
    transaction.transaction_instructions = parse_transaction_instructions(
        transaction_json, transaction._id
    )
    return transaction


def parse_transaction_accounts(transaction_json, transaction_id):
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


def parse_transaction_instructions(transaction_json, transaction_id):

    account_keys = transaction_json[TRANSACTION][MESSAGE][ACCOUNT_KEYS]
    return [
        InstructionTransaction(
            transaction_id=transaction_id,
            instruction_idx=idx,
            accounts=[account_keys[i] for i in instruction_json[ACCOUNTS]],
            data=instruction_json[DATA],
            program_account=account_keys[instruction_json[PROGRAM_ID_INDEX]],
        )
        for idx, instruction_json in enumerate(
            transaction_json[TRANSACTION][MESSAGE][INSTRUCTIONS]
        )
    ]


def dump(
    api_client: Client,
    blocks_slots: List[int],
    dump_dir: Path,
):
    for i, slot in enumerate(blocks_slots):
        try:
            print(f"Processing block {i+1}/{len(blocks_slots)}: {slot}")

            block_json = api_client.get_block(slot)
            if RESULT not in block_json:
                print("Skipped!")
                continue

            block_json = block_json[RESULT]
            block, block_transactions = parse_block(block_json, slot, FINALIZED)

            for transaction_json in tqdm(block_transactions):
                transaction = parse_transaction(transaction_json, slot)
                block.transactions.append(transaction)

            with open(dump_dir / f"{slot}.json", "w") as fp:
                json.dump(block.to_json(), fp)
        except:
            time.sleep(10)
