#!/usr/bin/env python3
"""
Tiny concurrent TCP SYN scanner.
Example:
    python port_scanner.py 192.168.1.0/24 22,80,443 --workers 200
"""

import argparse
import concurrent.futures
import ipaddress
import logging
import socket
from typing import List, Tuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Concurrent TCP port-scanner")
    p.add_argument("subnet", help="CIDR subnet, e.g. 10.0.0.0/24")
    p.add_argument(
        "ports",
        help="Comma-separated list of ports, e.g. 22,80,443",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=200,
        help="Thread-pool size (default: 200)",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=0.5,
        help="TCP connect timeout in seconds (default: 0.5)",
    )
    return p.parse_args()


def expand_targets(subnet: str, ports: str) -> List[Tuple[str, int]]:
    """Return all (ip, port) pairs to scan."""
    net = ipaddress.IPv4Network(subnet, strict=False)
    port_list = [int(p.strip()) for p in ports.split(",") if p.strip()]
    return [(str(ip), port) for ip in net.hosts() for port in port_list]


def check_port(ip: str, port: int, timeout: float) -> Tuple[str, int, bool]:
    """Try to connect; return (ip, port, is_open)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        res = sock.connect_ex((ip, port))
        return ip, port, res == 0


def main() -> None:
    args = parse_args()
    targets = expand_targets(args.subnet, args.ports)
    LOGGER.info("Scanning %d targets with %d workers", len(targets), args.workers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(check_port, ip, port, args.timeout) for ip, port in targets
        ]
        for fut in concurrent.futures.as_completed(futures):
            ip, port, is_open = fut.result()
            if is_open:
                LOGGER.info("OPEN %s:%d", ip, port)

    LOGGER.info("Scan complete")


if __name__ == "__main__":
    main()
