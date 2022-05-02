import matplotlib.pyplot as plt
import numpy as np

from scipy.cluster.hierarchy import dendrogram


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
        rotation = 0
    else:
        xticks, xtickslabels, rotation = ticks

    ax.set_xticks(xticks)
    ax.set_xticklabels(xtickslabels)
    ax.tick_params(axis="x", labelrotation=rotation)


def plot_dendrogram(model, **kwargs):
    # Create linkage matrix and then plot the dendrogram

    # create the counts of samples under each node
    counts = np.zeros(model.children_.shape[0])
    n_samples = len(model.labels_)
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1  # leaf node
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count

    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)

    # Plot the corresponding dendrogram
    dendrogram(linkage_matrix, **kwargs)
