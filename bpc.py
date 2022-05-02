from pathlib import Path

import numpy as np
from fastdtw import fastdtw
from matplotlib.lines import Line2D
from sklearn.cluster import DBSCAN
from tqdm import tqdm

from models import Block
from utils.constants import *


def get_vote_behavior(data_dir, epoch, slot_range):
    votes = {}
    for i, slot in tqdm(enumerate(slot_range)):
        block_file = data_dir / str(epoch) / "blocks" / f"{slot}.json"
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


def get_distance_matrix(votes):
    distances = np.zeros((len(votes), len(votes)))
    for i, v1 in tqdm(enumerate(votes)):
        for j, v2 in enumerate(votes):
            distance, _ = fastdtw(v1, v2)
            distances[i, j] = distance / max(len(v1), len(v2))

    return distances


def dbscan_cluster_vote_behavior(data_dir, epoch, slot_range, sensibility=2):
    votes = get_vote_behavior(data_dir, epoch, slot_range)
    first_votes = [votes[pubkey][FIRST_VOTE] for pubkey in list(votes.keys())[:100]]
    votes = [votes[pubkey][VOTES] for pubkey in list(votes.keys())[:100]]
    M = get_distance_matrix(votes)

    model = DBSCAN(eps=sensibility, metric="precomputed")

    labels = model.fit_predict(M)

    return votes, first_votes, labels
