import os

from solana.rpc.api import Client

CLUSTER = os.getenv("SOLANA_CLUSTER") or "devnet"


def test_connectivity():
    http_client = Client(f"https://api.{CLUSTER}.solana.com")
    assert http_client.is_connected(), f"Can't connect to the cluster {CLUSTER}"
