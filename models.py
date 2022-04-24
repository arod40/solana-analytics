from pathlib import Path
from typing import Dict, Union, List
from datetime import datetime

from utils import FINALIZED, CONFIRMED, PROCESSED, Model

class Epoch(Model):
    pass


class BlockStakeCommitment(Model):
    def __init__(self, stake_votes, total_epoch_active_stake):
        self.stake_votes = stake_votes
        self.total_epoch_active_stake = total_epoch_active_stake


class Transaction(Model):
    pass


class Block(Model):
    def __init__(
        self,
        commitment: Union[FINALIZED, CONFIRMED, PROCESSED],
        slot: int,
        blockhash: str,
        previous_blockhash: str,
        parent_slot: int,
        transactions: List[Transaction],
        signatures: List[str],
        rewards: List[Dict],
        block_time: datetime,
        block_height: int,
        stake_commitment: BlockStakeCommitment,
    ):
        self.commitment = commitment
        self.slot = slot
        self.blockhash = blockhash
        self.previous_blockhash = previous_blockhash
        self.parent_slot = parent_slot
        self.transactions = transactions
        self.signatures = signatures
        self.rewards = rewards
        self.block_time = block_time
        self.block_height = block_height
        self.stake_commitment = stake_commitment

    @classmethod
    def from_json(cls, json_str: Union[str, Path]):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError

    @property
    def can_change(self):
        return self.commitment != FINALIZED


class Account(Model):
    pass


class Cluster(Model):
    pass


class Node(Model):
    pass
