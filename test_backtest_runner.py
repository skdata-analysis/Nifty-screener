import os

from backtest_runner import (
    load_historical_snapshots
)


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

HISTORICAL_DIR = os.path.join(
    BASE_DIR,
    "data",
    "historical",
    "options"
)


print("\n==============================")
print("LOADING HISTORICAL SNAPSHOTS")
print("==============================")

snapshots = load_historical_snapshots(
    HISTORICAL_DIR
)

print(
    "Snapshots:",
    len(snapshots)
)

for i, snapshot in enumerate(
    snapshots[:5]
):

    print(
        i,
        snapshot["timestamp"],
        len(snapshot["data"]),
        "rows"
    )

print("\nHistorical loader working successfully.")
