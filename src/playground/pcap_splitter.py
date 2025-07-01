#!/usr/bin/env python3
"""
pcap_splitter.py
================
Split any .pcap / .pcapng into one file per TCP or UDP flow.

  python playground/pcap_splitter.py samples/dns_port.pcap out_dir/
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import pyshark
from scapy.utils import PcapWriter


# --------------------------------------------------------------------------- #
# helper
# --------------------------------------------------------------------------- #
def flow_key(pkt: pyshark.packet.packet.Packet) -> str | None:
    """
    tcp_10.0.0.1_1234_93.184.216.34_80
    udp_...
    """
    if "TCP" in pkt:
        layer = pkt.tcp
        proto = "tcp"
    elif "UDP" in pkt:
        layer = pkt.udp
        proto = "udp"
    else:
        return None
    return f"{proto}_{pkt.ip.src}_{layer.srcport}_{pkt.ip.dst}_{layer.dstport}"


# --------------------------------------------------------------------------- #
# core
# --------------------------------------------------------------------------- #
def split_pcap(pcap_path: Path, out_dir: Path) -> None:
    """
    Iterate through *pcap_path* and write each TCP/UDP flow to its own file
    inside *out_dir* using Scapy’s PcapWriter.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    capture = pyshark.FileCapture(
        str(pcap_path),
        keep_packets=False,
        include_raw=True,  # <-- needed for get_raw_packet()
        use_json=True,  # <-- tell TShark to output JSON so raw bytes are kept
    )

    writers: Dict[str, PcapWriter] = {}

    try:
        for pkt in capture:
            key = flow_key(pkt)
            if not key:
                continue

            if key not in writers:
                writers[key] = PcapWriter(
                    filename=str(out_dir / f"{key}.pcap"),
                    linktype=1,  # Ethernet
                    sync=True,
                )

            writers[key].write(pkt.get_raw_packet())
    finally:
        for w in writers.values():
            w.close()
        capture.close()


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Split pcap into individual flows")
    ap.add_argument("pcap", type=Path, help="Input .pcap / .pcapng file")
    ap.add_argument("outdir", type=Path, help="Directory for per-flow pcaps")
    return ap.parse_args()


def main() -> None:
    args = _parse_args()
    split_pcap(args.pcap, args.outdir)


if __name__ == "__main__":
    main()
