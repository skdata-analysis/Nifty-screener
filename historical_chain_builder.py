import glob
import os

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OPTIONS_DIR = os.path.join(BASE_DIR, "data", "historical", "options")
CHAINS_DIR = os.path.join(BASE_DIR, "data", "historical", "chains")
os.makedirs(CHAINS_DIR, exist_ok=True)


def _filename_strike(filename):
    for part in os.path.basename(filename).split("_"):
        try:
            return float(part)
        except ValueError:
            continue
    return None


def load_option_files():
    frames = []

    for file in sorted(glob.glob(os.path.join(OPTIONS_DIR, "*.csv"))):
        frame = pd.read_csv(file)
        filename = os.path.basename(file).upper()

        if "open_interest" not in frame.columns and "oi" in frame.columns:
            frame = frame.rename(columns={"oi": "open_interest"})

        if "strike" not in frame.columns:
            frame["strike"] = _filename_strike(file)

        if "option_type" not in frame.columns:
            if "_CE" in filename:
                frame["option_type"] = "CE"
            elif "_PE" in filename:
                frame["option_type"] = "PE"

        if "expiry" not in frame.columns:
            parts = os.path.basename(file).split("_")
            if len(parts) > 1:
                frame["expiry"] = parts[1]

        frames.append(frame)
        print(f"Loaded: {os.path.basename(file)} ({len(frame)} rows)")

    if not frames:
        raise RuntimeError("No historical option files found.")

    return pd.concat(frames, ignore_index=True)


def normalize_data(df):
    data = df.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")

    for column in [
        "strike", "open", "high", "low", "close", "volume",
        "open_interest", "lot_size"
    ]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    data["option_type"] = data["option_type"].astype(str).str.upper().str.strip()
    return data.dropna(subset=["timestamp", "strike", "option_type"])


def build_chain_snapshots(df):
    data = normalize_data(df)
    if data.empty:
        raise ValueError("No valid historical data available.")

    ce = data[data["option_type"] == "CE"][
        ["timestamp", "strike", "close", "volume", "open_interest"]
    ].rename(columns={
        "close": "ce_ltp", "volume": "ce_volume", "open_interest": "ce_oi"
    })

    pe = data[data["option_type"] == "PE"][
        ["timestamp", "strike", "close", "volume", "open_interest"]
    ].rename(columns={
        "close": "pe_ltp", "volume": "pe_volume", "open_interest": "pe_oi"
    })

    chain = pd.merge(
        ce, pe, on=["timestamp", "strike"], how="outer"
    ).sort_values(["timestamp", "strike"])

    if "expiry" in data.columns:
        expiries = data["expiry"].dropna().astype(str).unique()
        if len(expiries) > 0:
            chain["expiry"] = expiries[0]

    snapshot_count = 0
    for timestamp, snapshot in chain.groupby("timestamp"):
        timestamp_text = pd.Timestamp(timestamp).strftime("%Y-%m-%d_%H-%M")
        output_file = os.path.join(CHAINS_DIR, f"chain_{timestamp_text}.csv")
        snapshot.sort_values("strike").to_csv(output_file, index=False)
        snapshot_count += 1

    return chain, snapshot_count


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("HISTORICAL CHAIN BUILDER")
    print("=" * 50)
    print("\nOptions directory:")
    print(OPTIONS_DIR)
    print("\nLoading historical option files...")

    data = load_option_files()
    print("\nTotal rows:", len(data))
    print("Unique strikes:", data["strike"].nunique())
    print("Option types:", data["option_type"].unique().tolist())
    print("\nBuilding chain snapshots...")

    chain, snapshot_count = build_chain_snapshots(data)

    print("\n" + "=" * 50)
    print("SUCCESS")
    print("=" * 50)
    print("Combined rows:", len(chain))
    print("Snapshots created:", snapshot_count)
    print("\nSaved to:")
    print(CHAINS_DIR)
