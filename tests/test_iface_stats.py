# tests/test_iface_stats.py
from unittest.mock import mock_open, patch
from playground import iface_stats

# Sample output from /proc/net/dev
FAKE_PROC_NET_DEV = """
Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo: 12345    100    0    0    0     0          0         0    54321    100    0    0    0     0       0          0
  eth0: 67890    200    0    0    0     0          0         0    98765    200    0    0    0     0       0          0
"""

def test_get_stats_parser():
    """
    Test that the parser correctly extracts RX/TX bytes from a fake
    /proc/net/dev file content.
    """
    # Use patch to replace the built-in open function with a mock
    with patch("builtins.open", mock_open(read_data=FAKE_PROC_NET_DEV)):
        stats = iface_stats.get_stats()

    assert "lo" in stats
    assert "eth0" in stats
    assert stats["lo"]["rx"] == 12345
    assert stats["lo"]["tx"] == 54321
    assert stats["eth0"]["rx"] == 67890
    assert stats["eth0"]["tx"] == 98765

def test_get_stats_file_not_found():
    """
    Test that the function handles the FileNotFoundError gracefully
    if /proc/net/dev does not exist.
    """
    with patch("builtins.open", side_effect=FileNotFoundError):
        stats = iface_stats.get_stats()

    assert stats == {}
