from typing import Dict, Union, List

from utils import FINALIZED, CONFIRMED, PROCESSED, Model


class Block(Model):
    def __init__(
        self,
        slot: int,
        commitment: Union[FINALIZED, CONFIRMED, PROCESSED],
        blockhash: str,
        previous_blockhash: str,
        parent_slot: int,
        rewards: List[Dict],
        block_time: int,
        block_height: int,
        signatures: List[str],
        transactions: List,
    ):
        self.slot = slot
        self.commitment = commitment
        self.blockhash = blockhash
        self.previous_blockhash = previous_blockhash
        self.parent_slot = parent_slot
        self.rewards = rewards
        self.block_time = block_time
        self.block_height = block_height
        self.transactions = transactions
        self.signatures = signatures

    @property
    def _id(self):
        return self.slot

    @classmethod
    def from_dict(cls, dict: dict):
        return cls(
            slot=dict["slot"],
            commitment=dict["commitment"],
            blockhash=dict["blockhash"],
            previous_blockhash=dict["previous_blockhash"],
            parent_slot=dict["parent_slot"],
            rewards=dict["rewards"],
            block_time=dict["block_time"],
            block_height=dict["block_height"],
            transactions=[
                Transaction.from_json(tr_json) for tr_json in dict["transactions"]
            ],
            signatures=dict["signatures"],
        )

    def to_json(self):
        return {
            "slot": self.slot,
            "commitment": self.commitment,
            "blockhash": self.blockhash,
            "previous_blockhash": self.previous_blockhash,
            "parent_slot": self.parent_slot,
            "rewards": self.rewards,
            "block_time": self.block_time,
            "block_height": self.block_height,
            "transactions": self.transactions,
            "signatures": self.signatures,
            "transactions": [tr.to_json() for tr in self.transactions],
        }

    @property
    def can_change(self):
        return self.commitment != FINALIZED


class Transaction(Model):
    def __init__(
        self,
        signatures,
        err,
        fee,
        rewards,
        transaction_accounts=[],
        transaction_instructions=[],
        block=None,
    ):
        self.signatures = signatures
        self.block = block
        self.err = err
        self.fee = fee
        self.rewards = rewards
        self.transaction_accounts = transaction_accounts
        self.transaction_instructions = transaction_instructions

    @property
    def _id(self):
        return self.signatures[0]

    @classmethod
    def from_dict(cls, dict: dict):
        return cls(
            signatures=dict["signatures"],
            block=dict["block"],
            err=dict["err"],
            fee=dict["fee"],
            rewards=dict["rewards"],
            transaction_accounts=[
                AccountTransaction.from_json(tr_acc)
                for tr_acc in dict["transaction_accounts"]
            ],
            transaction_instructions=[
                InstructionTransaction.from_json(tr_inst)
                for tr_inst in dict["transaction_instructions"]
            ],
        )

    def to_json(self):
        return {
            "signatures": self.signatures,
            "block": self.block,
            "err": self.err,
            "fee": self.fee,
            "rewards": self.rewards,
            "transaction_accounts": [
                tr_acc.to_json() for tr_acc in self.transaction_accounts
            ],
            "transaction_instructions": [
                tr_inst.to_json() for tr_inst in self.transaction_instructions
            ],
        }


class AccountTransaction(Model):
    def __init__(
        self,
        transaction_id=None,
        pubkey=None,
        pre_balance=None,
        post_balance=None,
        read_only=None,
        signed=None,
        signature=None,
    ):
        self.pubkey = pubkey
        self.transaction_id = transaction_id
        self.pre_balance = pre_balance
        self.post_balance = post_balance
        self.read_only = read_only
        self.signed = signed
        self.signature = signature

    @property
    def _id(self):
        return (self.transaction_id, self.pubkey)

    @classmethod
    def from_dict(cls, dict: dict):
        return cls(
            transaction_id=dict["transaction_id"],
            pubkey=dict["pubkey"],
            pre_balance=dict["pre_balance"],
            post_balance=dict["post_balance"],
            read_only=dict["read_only"],
            signed=dict["signed"],
            signature=dict["signature"],
        )

    def to_json(self):
        return {
            "pubkey": self.pubkey,
            "transaction_id": self.transaction_id,
            "pre_balance": self.pre_balance,
            "post_balance": self.post_balance,
            "read_only": self.read_only,
            "signed": self.signed,
            "signature": self.signature,
        }


class InstructionTransaction(Model):
    def __init__(
        self,
        transaction_id=None,
        instruction_idx=None,
        accounts=None,
        data=None,
        program_account=None,
    ):
        self.transaction_id = transaction_id
        self.instruction_idx = instruction_idx
        self.accounts = accounts
        self.data = data
        self.program_account = program_account

    @property
    def _id(self):
        return (self.transaction_id, self.instruction_idx)

    @classmethod
    def from_dict(cls, dict: dict):
        return cls(
            transaction_id=dict["transaction_id"],
            instruction_idx=dict["instruction_idx"],
            accounts=dict["accounts"],
            data=dict["data"],
            program_account=dict["program_account"],
        )

    def to_json(self):
        return {
            "transaction_id": self.transaction_id,
            "instruction_idx": self.instruction_idx,
            "accounts": self.accounts,
            "data": self.data,
            "program_account": self.program_account,
        }


class BlockStakeCommitment(Model):
    def __init__(self, stake_votes, total_epoch_active_stake):
        self.stake_votes = stake_votes
        self.total_epoch_active_stake = total_epoch_active_stake
