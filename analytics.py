from cProfile import label
from pathlib import Path

import matplotlib.pyplot as plt

from models import Block
from utils.constants import *
from utils.plot import plot_bars

import json


def plot_rent_collected(data_dir, slot_range):
    results = {}
    for slot in slot_range:
        block: Block = Block.from_json(data_dir / f"{slot}.json")
        results[slot] = sum(
            [-rw[LAMPORTS] for rw in block.rewards if rw[REWARD_TYPE] == RENT]
        )

    _, ax = plt.subplots(1, 1)

    plot_bars(ax, results, "blue", "rent", move=0, width=0.25)
    ax.set_xlabel("slots")
    ax.set_ylabel("rent(lamports)")
    plt.legend()
    plt.show()


def plot_number_of_transactions(data_dir, slot_range):
    total = {}
    fail = {}
    for slot in slot_range:
        block: Block = Block.from_json(data_dir / f"{slot}.json")
        total[slot] = len(block.transactions)
        fail[slot] = len([tr for tr in block.transactions if tr.err is not None])

    _, ax = plt.subplots(1, 1)

    plot_bars(ax, total, "green", "total", move=0, width=0.25)
    plot_bars(ax, fail, "red", "fail", move=0, width=0.25)
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


if __name__ == "__main__":
    plot_rent_collected(Path("data"), list(range(131856396, 131856404)))
    plot_number_of_transactions(Path("data"), list(range(131856396, 131856404)))
    plot_leaders_pie_chart(Path("data"), 304)
