import numpy as np
from fastdtw import fastdtw
from sklearn.cluster import DBSCAN
from tqdm import tqdm

from utils.constants import *

def get_distance_matrix(votes):
    distances = np.zeros((len(votes), len(votes)))
    for i, v1 in tqdm(enumerate(votes)):
        for j, v2 in enumerate(votes):
            distance, _ = fastdtw(v1, v2)
            distances[i, j] = distance / max(len(v1), len(v2))

    return distances


def dbscan_cluster_vote_behavior(votes, sensibility=2):
    M = get_distance_matrix(votes)
    model = DBSCAN(eps=sensibility, metric="precomputed")
    return model.fit_predict(M)
