from cProfile import label
from collections import defaultdict
from pathlib import Path
from matplotlib.lines import Line2D

import matplotlib.pyplot as plt
import numpy as np
from bpc import dbscan_cluster_vote_behavior, get_vote_behavior

from models import Block, VoteInstruction
from utils.constants import *
from utils.plot import plot_bars

from tqdm import tqdm

import json


def plot_rent_collected(data_dir, slot_range):
    rent = {}
    given = {}
    for slot in tqdm(slot_range):
        block_file = data_dir / f"{slot}.json"
        if block_file.exists():
            block: Block = Block.from_json(block_file)
            rent[slot] = sum(
                [
                    -rw[LAMPORTS]
                    for rw in block.rewards
                    if rw[REWARD_TYPE] == RENT and rw[LAMPORTS] < 0
                ]
            )
            given[slot] = sum(
                [
                    rw[LAMPORTS]
                    for rw in block.rewards
                    if rw[REWARD_TYPE] == RENT and rw[LAMPORTS] > 0
                ]
            )
        else:
            rent[slot] = 0
            given[slot] = 0

    _, ax = plt.subplots(1, 1)

    labels = np.array(slot_range)
    xticks = np.linspace(0, len(labels) - 1, 5, dtype=np.int32)
    xtickslabels = [l for l in labels[xticks]]
    rotation = 0
    plot_bars(
        ax,
        rent,
        "blue",
        "rent",
        move=0,
        width=0.75,
        ticks=(xticks, xtickslabels, rotation),
    )
    plot_bars(
        ax,
        given,
        "green",
        "given",
        move=0,
        width=0.75,
        ticks=(xticks, xtickslabels, rotation),
    )
    ax.set_xlabel("slot")
    ax.set_ylabel("rent (lamports)")
    plt.legend()
    plt.show()


def plot_number_of_transactions(data_dir, slot_range):
    total = {}
    fail = {}
    for slot in tqdm(slot_range):
        block_file = data_dir / f"{slot}.json"
        if block_file.exists():
            block: Block = Block.from_json(block_file)
            total[slot] = len(block.transactions)
            fail[slot] = len([tr for tr in block.transactions if tr.err is not None])
        else:
            total[slot] = 0
            fail[slot] = 0

    _, ax = plt.subplots(1, 1)
    labels = np.array(slot_range)
    xticks = np.linspace(0, len(labels) - 1, 5, dtype=np.int32)
    xtickslabels = [l for l in labels[xticks]]
    rotation = 0
    plot_bars(
        ax,
        total,
        "green",
        "total",
        move=0,
        width=0.75,
        ticks=(xticks, xtickslabels, rotation),
    )
    plot_bars(
        ax,
        fail,
        "red",
        "fail",
        move=0,
        width=0.75,
        ticks=(xticks, xtickslabels, rotation),
    )
    ax.set_xlabel("slots")
    ax.set_ylabel("number of transactions")
    plt.legend()
    plt.show()


def plot_leaders_pie_chart(data_dir, epoch, other_share=1 / 3):
    schedule = json.loads((data_dir / str(epoch) / "leader_schedule.json").read_text())
    data = []
    total = 0
    for pubkey, slots in schedule.items():
        n = len(slots)
        data.append((n, pubkey))
        total += n

    data.sort(reverse=True)

    labels = []
    fracs = []
    acc = 0
    for num, pubkey in data:
        if acc / total >= 1 - other_share:
            labels.append("other")
            fracs.append(total - acc)
            break
        # labels.append(pubkey)
        labels.append(None)
        fracs.append(num)
        acc += num

    _, ax = plt.subplots(1, 1)
    ax.pie(fracs, labels=labels)

    plt.show()


def plot_validator_block_production(data_dir, epoch, slot_range):
    schedule = json.loads((data_dir / str(epoch) / "leader_schedule.json").read_text())
    schedule_inv = {
        slot: pubkey for pubkey, slots in schedule.items() for slot in slots
    }
    total = defaultdict(int)
    missed = defaultdict(int)

    existing_blocks = set()
    for slot in tqdm(slot_range):
        if (data_dir / str(epoch) / "blocks" / f"{slot}.json").exists():
            existing_blocks.add(slot)

    for slot in slot_range:
        total[schedule_inv[slot]] += 1
        if slot not in existing_blocks:
            missed[schedule_inv[slot]] += 1

    _, ax = plt.subplots(1, 1)
    labels = np.array(list(total.keys()))
    xticks = []
    xtickslabels = []
    rotation = 0
    plot_bars(
        ax,
        total,
        "green",
        "assigned",
        move=0,
        width=0.75,
        ticks=(xticks, xtickslabels, rotation),
    )
    plot_bars(
        ax,
        missed,
        "red",
        "missed",
        move=0,
        width=0.75,
        ticks=(xticks, xtickslabels, rotation),
    )

    ax.set_xlabel("validator")
    ax.set_ylabel("leader slots")
    plt.legend()
    plt.show()


def plot_validators_voting(data_dir, epoch, slot_range, validators):
    votes = get_vote_behavior(data_dir, epoch, slot_range)

    _, ax = plt.subplots(1, 1)
    for validator in validators:
        first_vote = votes[validator][FIRST_VOTE]
        validator_votes = votes[validator][VOTES]
        ax.plot(
            range(first_vote, first_vote + len(validator_votes)),
            [vote - slot_range[0] for vote in validator_votes],
            label=f"{validator[:10]}...",
        )

    ax.set_xlabel("slot")
    ax.set_ylabel("max slot voted")
    plt.legend()
    plt.show()


def plot_voting_outlier_behavior(data_dir, epoch, slot_range, sensibility=2):
    votes, first_votes, labels = dbscan_cluster_vote_behavior(
        data_dir, epoch, slot_range, sensibility=sensibility
    )
    for validator_votes, first_vote, cl in zip(votes, first_votes, labels):
        if cl == -1:
            plt.plot(
                range(first_vote, first_vote + len(validator_votes)),
                [vote - slot_range[0] for vote in validator_votes],
                color="red",
            )
        else:
            plt.plot(
                range(first_vote, first_vote + len(validator_votes)),
                [vote - slot_range[0] for vote in validator_votes],
                color="blue",
            )

    plt.xlabel("slot")
    plt.ylabel("max slot voted")
    custom_lines = [
        Line2D([0], [0], color="blue", lw=4),
        Line2D([0], [0], color="red", lw=4),
    ]

    plt.legend(custom_lines, ["normal", "outliers"])
    plt.show()


if __name__ == "__main__":
    # plot_rent_collected(Path("data/305/blocks"), list(range(131760000, 131760100)))
    # plot_number_of_transactions(
    #     Path("data/305/blocks"), list(range(131760000, 131760980))
    # )
    # plot_leaders_pie_chart(Path("data"), 305)
    # plot_validator_block_production(
    #     Path("data"), 305, list(range(131760000, 131760980))
    # )
    # plot_validators_voting(
    #     Path("data"),
    #     305,
    #     range(131760000, 131760100),
    #     [
    #         "4o27cX8MsYmyzbYq9V5a2aMTW6eC4wxonVfkik6xGYHD",
    #         "H2oJUXwghyv6BwZH68jobU8jGutBji4v3WbPA96kc5Yd",
    #         "6bdb3cRscVm1HTNNvgR8bumjSsQd2fbuFjwANtCLHC8f",
    #         "AKxcADuF5Fvfidz9jvsN53dFJchjKQQJbhK3jMtacQML",
    #     ],
    # )

    plot_voting_outlier_behavior(
        Path("data"), 305, range(131760000, 131760100), sensibility=2
    )
