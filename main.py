from solana.rpc.api import Client

from config import CLUSTER
from reports import BlockCommitmentReport, BlocksReport
from utils.constants import FINALIZED

http_client = Client(f"https://api.{CLUSTER}.solana.com")
# epoch_info = http_client.get_epoch_info(commitment=FINALIZED)
# slot = epoch_info["result"]["absoluteSlot"]

# report = BlockCommitmentReport.capture({}, http_client, [slot])
# report.plot()


report = BlocksReport.capture({}, http_client, [129670496])
