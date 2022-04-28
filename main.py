from solana.rpc.api import Client

from config import CLUSTER
from reports import BlockCommitmentReport, BlocksReport
from utils.constants import FINALIZED

http_client = Client(f"https://api.{CLUSTER}.solana.com")

print(CLUSTER)

least_recent = http_client.get_first_available_block()["result"]
most_rescent = http_client.get_epoch_info(commitment=FINALIZED)["result"][
    "absoluteSlot"
]
print(3 * len(range(most_rescent - least_recent)) / 2**20)
print(
    least_recent,
    most_rescent,
)

# report = BlockCommitmentReport.capture({}, http_client, [slot])
# report.plot()


report = BlocksReport.capture({}, http_client, [129670496])


import json

with open("a.json", "w") as fp:
    json.dump(report.to_json(), fp)
