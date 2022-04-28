from pathlib import Path
from typing import Dict, Union, List
from datetime import datetime

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
        signatures: List[str] = [],
        transactions: List = [],
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
    def from_json(cls, json_str: Union[str, Path]):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError

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


class Account(Model):
    def __init__(
        self, pubkey, executable, owner, rent_epoch, data, account_transactions=[]
    ):
        self.pubkey = pubkey
        self.executable = executable
        self.owner = owner
        self.rent_epoch = rent_epoch
        self.data = data
        self.account_transactions = account_transactions

    @property
    def _id(self):
        return self.pubkey


class AccountTransaction(Model):
    def __init__(
        self,
        pre_balance,
        post_balance,
        read_only,
        signed,
        transaction_id=None,
        account_id=None,
        signature=None,
    ):
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.pre_balance = pre_balance
        self.post_balance = post_balance
        self.read_only = read_only
        self.signed = signed
        self.signature = signature

    @property
    def _id(self):
        return (self.transaction_id, self.account_id)


class BlockStakeCommitment(Model):
    def __init__(self, stake_votes, total_epoch_active_stake):
        self.stake_votes = stake_votes
        self.total_epoch_active_stake = total_epoch_active_stake


class Instruction(Model):
    pass


class InstructionAccount(Model):
    pass
