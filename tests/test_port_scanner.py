# tests/test_port_scanner.py
import sys
import pytest
from playground import port_scanner


def test_expand_targets():
    pairs = port_scanner.expand_targets("192.0.2.0/30", "80,443")
    assert len(pairs) == 4  # 2 hosts × 2 ports
    assert ("192.0.2.1", 80) in pairs
    assert ("192.0.2.2", 443) in pairs


def test_sync_worker_closed_port():
    # 8.8.8.8:1 is almost certainly closed
    assert not port_scanner._scan_ip_port("8.8.8.8", 1, 0.2)


def test_scan_ip_port_open(mocker):
    """Patch socket.socket so no real network traffic occurs."""
    mock_sock = mocker.patch("socket.socket")

    inst = mock_sock.return_value
    inst.connect_ex.return_value = 0  # “open”

    is_open = port_scanner._scan_ip_port("1.2.3.4", 22, 0.1)
    assert is_open
    inst.settimeout.assert_called_once_with(0.1)
    inst.connect_ex.assert_called_once_with(("1.2.3.4", 22))
    inst.close.assert_called_once()


@pytest.mark.asyncio
async def test_async_worker_closed_port():
    ok = await port_scanner._async_scan("8.8.8.8", 1, 0.2)
    assert not ok


def test_benchmark_flag_runs(monkeypatch):
    args = [
        "127.0.0.1/32",
        "80",
        "--benchmark",
        "--mode",
        "thread",
        "--workers",
        "1",
    ]
    monkeypatch.setattr(sys, "argv", ["port_scanner.py", *args])
    # Should finish without raising
    port_scanner.main()
