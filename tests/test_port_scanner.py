from playground import port_scanner


def test_expand_targets():
    pairs = port_scanner.expand_targets("192.0.2.0/30", "80,443")
    assert len(pairs) == 4  # 2 hosts × 2 ports
    assert ("192.0.2.1", 80) in pairs
    assert ("192.0.2.2", 443) in pairs


def test_check_port_open(mocker):
    # Patch socket.socket so no real network calls happen
    mock_sock = mocker.patch("socket.socket")

    # Configure connect_ex to return 0 (open)
    instance = mock_sock.return_value.__enter__.return_value
    instance.connect_ex.return_value = 0

    ip, port, is_open = port_scanner.check_port("1.2.3.4", 22, 0.1)
    assert is_open
    instance.settimeout.assert_called_once_with(0.1)
    instance.connect_ex.assert_called_once_with(("1.2.3.4", 22))
