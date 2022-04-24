from config import *
from solana.rpc.api import Client


def test_connectivity():
    http_client = Client(f"https://api.{CLUSTER}.solana.com")
    assert http_client.is_connected(), f"Can't connect to the cluster {CLUSTER}"
