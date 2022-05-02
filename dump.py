"""
Usage:
    dump.py --cluster=<str> --epoch=<int> --data-dir=<file> [options]

Options:
    -h --help                                                    show this screen.
    --cluster=['mainnet-beta' | 'devnet' | 'testnet']            name of the Solana cluster to target (mainnet-beta / devnet / testnet)
    --epoch=<int>                                                epoch to capture
    --data-dir=<file>                                            directory to store the data
    --from-slot=<int>                                            initial slot to capture [default: 0]
    --total-slots=<int>                                          number of slots to capture, default all of them [default: -1]
"""


from argparse import ArgumentError
import json
import time
from pathlib import Path
from typing import List

from docopt import docopt
from solana.exceptions import SolanaRpcException
from solana.rpc.api import Client
from tqdm import tqdm

from models import AccountTransaction, Block, InstructionTransaction, Transaction
from utils.constants import *


def get_epoch_bounds(api_client: Client, epoch: int):
    epoch_info = api_client.get_epoch_info()[RESULT]
    epoch_schedule = api_client.get_epoch_schedule()[RESULT]
    current_epoch = epoch_info[EPOCH]
    first_normal_epoch = epoch_schedule[FIRST_NORMAL_EPOCH]
    if not (first_normal_epoch <= epoch <= current_epoch):
        raise ArgumentError("Epoch does not exist yet or it was not of stable length")

    first_normal_slot = epoch_schedule[FIRST_NORMAL_EPOCH]
    slots_per_epoch = epoch_schedule[SLOTS_PER_EPOCH]

    low_bound = first_normal_slot + slots_per_epoch * (epoch - first_normal_epoch)
    up_bound = low_bound + slots_per_epoch

    return low_bound, up_bound


def parse_block(block_json, slot, commitment):
    return (
        Block(
            slot=slot,
            commitment=commitment,
            blockhash=block_json[BLOCKHASH],
            previous_blockhash=block_json[PREVIOUS_BLOCKHASH],
            parent_slot=block_json[PARENT_SLOT],
            block_time=block_json[BLOCK_TIME],
            block_height=block_json[BLOCK_HEIGHT],
            rewards=block_json[REWARDS],
            transactions=[],
            signatures=[],
        ),
        block_json[TRANSACTIONS],
    )


def parse_transaction(transaction_json, slot):
    transaction = Transaction(
        block=slot,
        signatures=transaction_json[TRANSACTION][SIGNATURES],
        err=transaction_json[META][ERR],
        fee=transaction_json[META][FEE],
        rewards=transaction_json[META][REWARDS],
        transaction_instructions=transaction_json[TRANSACTION][MESSAGE][INSTRUCTIONS],
    )
    transaction.transaction_accounts = parse_transaction_accounts(
        transaction_json, transaction._id
    )
    transaction.transaction_instructions = parse_transaction_instructions(
        transaction_json, transaction._id
    )
    return transaction


def parse_transaction_accounts(transaction_json, transaction_id):
    account_keys = transaction_json[TRANSACTION][MESSAGE][ACCOUNT_KEYS]
    pre_balances = transaction_json[META][PRE_BALANCES]
    posts_balances = transaction_json[META][POST_BALANCES]
    signatures = transaction_json[TRANSACTION][SIGNATURES] + [None] * (
        len(account_keys)
    )
    return [
        AccountTransaction(
            transaction_id=transaction_id,
            pubkey=key_info[PUBKEY],
            pre_balance=pre_balance,
            post_balance=post_balance,
            read_only=not key_info[WRITABLE],
            signed=key_info[SIGNER],
            signature=signature,
        )
        for key_info, pre_balance, post_balance, signature in zip(
            account_keys, pre_balances, posts_balances, signatures
        )
    ]


def parse_transaction_instructions(transaction_json, transaction_id):

    account_keys = transaction_json[TRANSACTION][MESSAGE][ACCOUNT_KEYS]

    return [
        InstructionTransaction(
            data=instruction_json[DATA]
            if DATA in instruction_json
            else instruction_json[PARSED],
            program_account=account_keys[instruction_json[PROGRAM_ID_INDEX]]
            if PROGRAM_ID_INDEX in instruction_json
            else instruction_json[PROGRAM_ID],
            accounts=instruction_json[ACCOUNTS]
            if ACCOUNTS in instruction_json
            else None,
            program_name=instruction_json[PROGRAM]
            if PROGRAM in instruction_json
            else None,
        )
        for idx, instruction_json in enumerate(
            transaction_json[TRANSACTION][MESSAGE][INSTRUCTIONS]
        )
    ]


def dump_blocks(
    api_client: Client,
    blocks_slots: List[int],
    dump_dir: Path,
):
    for i, slot in enumerate(blocks_slots):
        try:
            print(f"Processing block {i+1}/{len(blocks_slots)}: {slot}")

            block_json = api_client.get_block(slot, encoding="jsonParsed")
            if RESULT not in block_json:
                print("Skipped!")
                continue

            block_json = block_json[RESULT]
            block, block_transactions = parse_block(block_json, slot, FINALIZED)

            for transaction_json in tqdm(block_transactions):
                transaction = parse_transaction(transaction_json, slot)
                block.transactions.append(transaction)

            with open(dump_dir / f"{slot}.json", "w") as fp:
                json.dump(block.to_json(), fp)
        except SolanaRpcException:
            time.sleep(10)
        except Exception as e:
            raise e


def dump_epoch_leader_schedule(api_client: Client, first_slot: int, dump_dir: Path):
    leader_schedule = api_client.get_leader_schedule(first_slot)[RESULT]
    leader_schedule = {
        pubkey: [first_slot + slot_offset for slot_offset in slots]
        for pubkey, slots in leader_schedule.items()
    }
    with open(dump_dir / f"leader_schedule.json", "w") as fp:
        json.dump(leader_schedule, fp)


def dump_epoch(
    api_client: Client, epoch: int, dump_dir: Path, from_slot=0, total_slots=-1
):
    epoch_bounds = get_epoch_bounds(http_client, epoch)
    low_bound, up_bound = epoch_bounds

    dump_dir = dump_dir / str(epoch)
    dump_dir.mkdir(parents=True, exist_ok=True)

    if total_slots == -1:
        total_slots = up_bound - low_bound

    blocks_dir = dump_dir / "blocks"
    blocks_dir.mkdir(parents=True, exist_ok=True)
    dump_blocks(
        api_client,
        list(range(low_bound, up_bound))[from_slot : from_slot + total_slots],
        blocks_dir,
    )
    dump_epoch_leader_schedule(api_client, low_bound, dump_dir)


if __name__ == "__main__":
    args = docopt(__doc__)
    cluster = args["--cluster"]
    if cluster not in [MAINNET, DEVNET, TESTNET]:
        raise ArgumentError(
            f"--cluster must be one of '{MAINNET}', '{DEVNET}', '{TESTNET}'"
        )
    http_client = Client(f"https://api.{cluster}.solana.com")

    dump_epoch(
        http_client,
        int(args["--epoch"]),
        Path(args["--data-dir"]),
        int(args["--from-slot"]),
        int(args["--total-slots"]),
    )
