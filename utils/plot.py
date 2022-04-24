import matplotlib.pyplot as plt
import numpy as np


def plot_bars(
    ax,
    results,
    color=None,
    label=None,
    move=-1,
    width=1,
    ticks=None,
):
    labels = np.array(list(results.keys()))
    X = np.arange(len(labels))  # the label locations
    y = [results[key] for key in labels]

    ax.bar(X + move * width / 2, y, width, label=label, color=color)

    if ticks is None:
        xticks = np.array(range(len(labels)))
        xtickslabels = labels[xticks]
    else:
        xticks, xtickslabels = ticks

    ax.set_xticks(xticks)
    ax.set_xticklabels(xtickslabels)
