from http.client import responses
from typing import List, Union

from solana.rpc.api import Client

from utils import JSONable, Report
from models import BlockStakeCommitment

import matplotlib.pyplot as plt

from utils.constants import COMMITMENT, RESULT, TOTAL_STAKE
from utils.plot import plot_bars


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
