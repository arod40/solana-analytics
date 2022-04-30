from pathlib import Path

import matplotlib.pyplot as plt

from models import Block
from utils.constants import *
from utils.plot import plot_bars


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


if __name__ == "__main__":
    plot_rent_collected(Path("data"), list(range(131856396, 131856404)))
