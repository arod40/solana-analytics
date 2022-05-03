import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from tqdm import tqdm

from bpc import dbscan_cluster_vote_behavior
from models import Block
from utils.constants import *
from utils.file import get_block_file, get_leader_schedule_file
from utils.plot import plot_bars


def get_vote_behavior(data_dir, epoch, slot_range):
    votes = {}
    for i, slot in tqdm(enumerate(slot_range)):
        block_file = get_block_file(data_dir, epoch, slot)
        if block_file.exists():
            block = Block.from_json(block_file)
            for validator in votes:
                votes[validator][VOTES].append(votes[validator][VOTES][-1])

            for vote in [
                tr_inst.data[INFO]
                for tr in block.transactions
                for tr_inst in tr.transaction_instructions
                if tr.err is None
                and tr_inst.program_account == VOTE_PROGRAM_ACCOUNT
                and tr_inst.data[TYPE] == VOTE
            ]:
                authority = vote[VOTE_AUTHORITY]
                vote_slot = vote[VOTE][SLOTS][-1]
                if authority not in votes:
                    votes[authority] = {FIRST_VOTE: i + 1, VOTES: [vote_slot]}
                else:
                    votes[authority][VOTES][-1] = vote_slot

    return votes


def plot_rent_collected(data_dir, epoch, slot_range):
    rent = {}
    given = {}
    for slot in tqdm(slot_range):
        block_file = get_block_file(data_dir, epoch, slot)
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


def plot_number_of_transactions(data_dir, epoch, slot_range):
    total = {}
    fail = {}
    for slot in tqdm(slot_range):
        block_file = get_block_file(data_dir, epoch, slot)
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
    schedule = json.loads(get_leader_schedule_file(data_dir, epoch).read_text())
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
    schedule = json.loads(get_leader_schedule_file(data_dir, epoch).read_text())
    schedule_inv = {
        slot: pubkey for pubkey, slots in schedule.items() for slot in slots
    }
    total = defaultdict(int)
    missed = defaultdict(int)

    existing_blocks = set()
    for slot in tqdm(slot_range):
        if get_block_file(data_dir, epoch, slot).exists():
            existing_blocks.add(slot)

    for slot in slot_range:
        total[schedule_inv[slot]] += 1
        if slot not in existing_blocks:
            missed[schedule_inv[slot]] += 1

    _, ax = plt.subplots(1, 1)
    # labels = np.array(list(total.keys()))
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
    votes = get_vote_behavior(data_dir, epoch, slot_range)
    validators = list(votes.keys())[:100]

    first_votes = [votes[pubkey][FIRST_VOTE] for pubkey in validators]
    votes = [votes[pubkey][VOTES] for pubkey in validators]

    labels = dbscan_cluster_vote_behavior(votes, sensibility=sensibility)
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
    CLI = argparse.ArgumentParser()
    CLI.add_argument(
        "plot",
        choices=["rent", "transactions", "leaders", "production", "votes", "outliers"],
    )
    CLI.add_argument("--data-dir", type=str, required=True)
    CLI.add_argument(
        "--slot-range",
        nargs=2,
        type=int,
        default=[0, -1],
    )
    CLI.add_argument(
        "--validators",
        nargs="+",
        type=str,
    )
    CLI.add_argument(
        "--epoch",
        type=int,
    )
    CLI.add_argument(
        "--other-share",
        type=float,
        default=1 / 3,
    )
    CLI.add_argument(
        "--sensibility",
        type=int,
        default=2,
    )

    # parse the command line
    args = CLI.parse_args()

    if args.plot == "rent":
        plot_rent_collected(
            Path(args.data_dir),
            args.epoch,
            list(range(*args.slot_range)),
        )
    elif args.plot == "transactions":
        plot_number_of_transactions(
            Path(args.data_dir),
            args.epoch,
            list(range(*args.slot_range)),
        )
    elif args.plot == "leaders":
        plot_leaders_pie_chart(
            Path(args.data_dir), args.epoch, other_share=args.other_share
        )
    elif args.plot == "production":
        plot_validator_block_production(
            Path(args.data_dir),
            args.epoch,
            list(range(*args.slot_range)),
        )
    elif args.plot == "votes":
        plot_validators_voting(
            Path(args.data_dir),
            args.epoch,
            list(range(*args.slot_range)),
            args.validators,
        )
    elif args.plot == "outliers":

        plot_voting_outlier_behavior(
            Path(args.data_dir),
            args.epoch,
            list(range(*args.slot_range)),
            sensibility=args.sensibility,
        )
    else:
        raise Exception("Invalid operation")
