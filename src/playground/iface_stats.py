#!/usr/bin/env python3
"""
iface_stats.py
==============
Prints RX/TX bytes/sec for network interfaces by reading /proc/net/dev.
"""

import time
import argparse
from pathlib import Path
from typing import Dict, Any

# ── logging ────────────────────────────────────────────────────────────────────
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
LOG = logging.getLogger(Path(__file__).stem)


def get_stats() -> Dict[str, Dict[str, int]]:
    """
    Parses /proc/net/dev and returns a dict of:
    {iface: {'rx': bytes, 'tx': bytes}}
    """
    stats: Dict[str, Dict[str, int]] = {}
    try:
        with open("/proc/net/dev") as f:
            lines = f.readlines()
            for line in lines:
                if ":" not in line:
                    continue
                parts = line.split(":")
                iface_name = parts[0].strip()
                data = parts[1].split()
                stats[iface_name] = {
                    "rx": int(data[0]),
                    "tx": int(data[8]),
                }
    except FileNotFoundError:
        LOG.error("Could not find /proc/net/dev. This script only works on Linux.")
        return {}
    return stats


def main() -> None:
    """Main loop to calculate and print stats."""
    parser = argparse.ArgumentParser(
        description="Print RX/TX stats for network interfaces."
    )
    parser.add_argument(
        "-i",
        "--interface",
        type=str,
        help="Specific interface to monitor (e.g., eth0). Default is all.",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between updates (default: 1.0)",
    )
    args = parser.parse_args()

    try:
        LOG.info("Starting network statistics monitoring. Press Ctrl+C to exit.")
        last_stats = get_stats()
        if not last_stats:
            return

        time.sleep(args.delay)

        while True:
            current_stats = get_stats()
            if not current_stats:
                break

            print("-" * 50)
            interfaces = (
                [args.interface] if args.interface in current_stats else sorted(current_stats.keys())
            )

            for iface in interfaces:
                if iface not in last_stats:
                    continue

                last = last_stats[iface]
                current = current_stats[iface]

                rx_rate = (current["rx"] - last["rx"]) / args.delay / 1024  # KB/s
                tx_rate = (current["tx"] - last["tx"]) / args.delay / 1024  # KB/s

                print(f"{iface:<12} RX: {rx_rate:8.2f} KB/s | TX: {tx_rate:8.2f} KB/s")

            last_stats = current_stats
            time.sleep(args.delay)

    except KeyboardInterrupt:
        print()
        LOG.info("Monitoring stopped.")


if __name__ == "__main__":
    main()
