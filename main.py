from solana.rpc.api import Client

from config import *

http_client = Client(f"https://api.{CLUSTER}.solana.com")
epoch_info = http_client.get_epoch_info(commitment="finalized")
print(epoch_info)
