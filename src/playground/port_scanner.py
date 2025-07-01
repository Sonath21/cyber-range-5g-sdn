#!/usr/bin/env python3
"""
Concurrent TCP scanner with three back-ends:

    python port_scanner.py 192.168.1.0/24 22,80 --mode thread      --workers 200
    python port_scanner.py 192.168.1.0/24 22,80 --mode asyncio     --workers 800
    python port_scanner.py 192.168.1.0/24 22,80 --mode process     --workers 32
    python port_scanner.py 10.0.0.0/24 22,80 --mode asyncio --benchmark
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import ipaddress
import logging
import multiprocessing
import socket
import time
from pathlib import Path
from typing import List, Tuple

# ── logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
LOG = logging.getLogger(Path(__file__).stem)


# ── CLI parsing ────────────────────────────────────────────────────────────────
def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Concurrent TCP port-scanner")
    p.add_argument("subnet", help="CIDR subnet, e.g. 10.0.0.0/24")
    p.add_argument("ports", help="Comma-separated port list, e.g. 22,80,443")
    p.add_argument("--workers", type=int, default=200, help="Pool size (default 200)")
    p.add_argument("--timeout", type=float, default=0.5, help="TCP timeout (s)")
    p.add_argument(
        "--mode",
        choices=["thread", "asyncio", "process"],
        default="thread",
        help="Concurrency back-end",
    )
    p.add_argument(
        "--benchmark",
        action="store_true",
        help="Time the scan and print duration only",
    )
    return p.parse_args()


# ── helpers ────────────────────────────────────────────────────────────────────
def _timed(func, *a, **kw):
    t0 = time.perf_counter()
    out = func(*a, **kw)
    return out, time.perf_counter() - t0


def _scan_ip_port(ip: str, port: int, timeout: float) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    res = sock.connect_ex((ip, port))
    sock.close()
    return res == 0


def expand_targets(subnet: str, ports: str) -> List[Tuple[str, int]]:
    net = ipaddress.IPv4Network(subnet, strict=False)
    plist = [int(p.strip()) for p in ports.split(",") if p.strip()]
    return [(str(ip), port) for ip in net.hosts() for port in plist]


# ── async back-end ─────────────────────────────────────────────────────────────
async def _async_scan(ip: str, port: int, timeout: float) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False


async def _async_runner(targets, timeout, workers):
    sem = asyncio.Semaphore(workers)

    async def limited(ip, port):
        async with sem:
            return await _async_scan(ip, port, timeout)

    coros = [limited(ip, port) for ip, port in targets]
    return await asyncio.gather(*coros)


# ── thread & process back-ends ────────────────────────────────────────────────
def _thread_runner(targets, timeout, workers):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda t: _scan_ip_port(*t, timeout), targets))


def _process_runner(targets, timeout, workers):
    with multiprocessing.Pool(processes=workers) as pool:
        return pool.starmap(
            _scan_ip_port, [(ip, port, timeout) for ip, port in targets]
        )


# ── main orchestrator ─────────────────────────────────────────────────────────
def main() -> None:
    args = _parse_args()
    targets = expand_targets(args.subnet, args.ports)
    LOG.info(
        "Targets: %d   Workers: %d   Mode: %s", len(targets), args.workers, args.mode
    )

    # choose the runner --------------------------------------------------------
    def run_thread():
        return _thread_runner(targets, args.timeout, args.workers)

    def run_asyncio():
        return asyncio.run(_async_runner(targets, args.timeout, args.workers))

    def run_process():
        return _process_runner(targets, args.timeout, args.workers)

    if args.mode == "thread":
        runner = run_thread
    elif args.mode == "asyncio":
        runner = run_asyncio
    else:  # "process"
        runner = run_process

    # benchmark only? ----------------------------------------------------------
    if args.benchmark:
        _, dur = _timed(runner)
        LOG.info(
            "Benchmark: mode=%s  %.3f s  (%d checks)", args.mode, dur, len(targets)
        )
        return

    # normal scan --------------------------------------------------------------
    results, dur = _timed(runner)
    for (ip, port), is_open in zip(targets, results):
        if is_open:
            LOG.info("OPEN  %s:%d", ip, port)

    LOG.info("Scan finished in %.3f s", dur)


if __name__ == "__main__":
    main()
