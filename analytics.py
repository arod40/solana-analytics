from cProfile import label
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

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

    _, ax = plt.subplots(1, 1)

    plot_bars(ax, rent, "blue", "rent", move=0, width=0.75)
    plot_bars(ax, given, "green", "given", move=0, width=0.75)
    ax.set_xlabel("slots")
    ax.set_ylabel("rent(lamports)")
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

    _, ax = plt.subplots(1, 1)

    plot_bars(ax, total, "green", "total", move=0, width=0.75)
    plot_bars(ax, fail, "red", "fail", move=0, width=0.75)
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
        labels.append(pubkey)
        fracs.append(num)
        acc += num

    _, ax = plt.subplots(1, 1)
    ax.pie(fracs, labels=labels)

    plt.show()


def plot_validator_block_production(data_dir, epoch, slots_range):
    schedule = json.loads((data_dir / str(epoch) / "leader_schedule.json").read_text())
    schedule_inv = {
        slot: pubkey for pubkey, slots in schedule.items() for slot in slots
    }
    total = defaultdict(int)
    missed = defaultdict(int)

    existing_blocks = set()
    for slot in slots_range:
        if (data_dir / str(epoch) / "blocks" / f"{slot}.json").exists():
            existing_blocks.add(slot)

    for slot in slots_range:
        total[schedule_inv[slot]] += 1
        if slot not in existing_blocks:
            missed[schedule_inv[slot]] += 1

    _, ax = plt.subplots(1, 1)
    plot_bars(ax, total, "green", "assigned", move=0, width=0.75)
    plot_bars(ax, missed, "red", "missed", move=0, width=0.75)

    plt.legend()
    plt.show()


def plot_validators_voting(data_dir, epoch, slots_range, validators):
    votes = {pubkey: {"X": [], "y": []} for pubkey in validators}
    for slot in tqdm(slots_range):
        block_file = data_dir / str(epoch) / "blocks" / f"{slot}.json"
        if block_file.exists():
            block = Block.from_json(block_file)
            for vote in [
                tr_inst.data[INFO]
                for tr in block.transactions
                for tr_inst in tr.transaction_instructions
                if tr_inst.program_account == VOTE_PROGRAM_ACCOUNT
                and tr_inst.data[TYPE] == VOTE
            ]:
                authority = vote[VOTE_AUTHORITY]
                vote_slots = vote[VOTE][SLOTS]
                if authority in validators:
                    votes[authority]["X"] += [slot] * len(vote_slots)
                    votes[authority]["y"] += vote_slots

    _, ax = plt.subplots(1, 1)
    colors = [f"C{i}" for i in range(len(validators))]
    for validator, color in zip(validators, colors):
        ax.scatter(
            votes[validator]["X"],
            votes[validator]["y"],
            color=color,
            label=f"{validator[:10]}...",
        )

    ax.set_xlabel("slot voted in")
    ax.set_ylabel("slot voted for")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    plot_rent_collected(Path("data/304/blocks"), list(range(131328000, 131329000)))
    plot_number_of_transactions(
        Path("data/304/blocks"), list(range(131328000, 131329000))
    )
    plot_leaders_pie_chart(Path("data"), 304)
    plot_validator_block_production(
        Path("data"), 304, list(range(131328000, 131329000))
    )
    plot_validators_voting(
        Path("data"),
        305,
        range(131760000, 131760100),
        [
            "4o27cX8MsYmyzbYq9V5a2aMTW6eC4wxonVfkik6xGYHD",
            "H2oJUXwghyv6BwZH68jobU8jGutBji4v3WbPA96kc5Yd",
            "6bdb3cRscVm1HTNNvgR8bumjSsQd2fbuFjwANtCLHC8f",
            "AKxcADuF5Fvfidz9jvsN53dFJchjKQQJbhK3jMtacQML",
        ],
    )
