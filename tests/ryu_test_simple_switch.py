# tests/ryu_test_simple_switch.py
import pytest
from unittest.mock import MagicMock, patch

from ryu_app.simple_switch import SimpleSwitch
from ryu.controller import ofp_event
from ryu.lib.packet import packet, ethernet, ether_types
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser

@pytest.fixture
def simple_switch():
    """Fixture to create a SimpleSwitch instance for testing."""
    with patch('ryu.base.app_manager.RyuApp.__init__'):
        app = SimpleSwitch()
        app.logger = MagicMock()
        return app

def test_switch_features_handler(simple_switch):
    """Test the switch features handler to ensure the table-miss flow is added."""
    mock_datapath = MagicMock()
    mock_datapath.ofproto = MagicMock()
    mock_datapath.ofproto_parser = MagicMock()
    mock_match = MagicMock()
    mock_actions = [MagicMock()]
    mock_datapath.ofproto_parser.OFPMatch.return_value = mock_match
    mock_datapath.ofproto_parser.OFPActionOutput.return_value = mock_actions[0]
    mock_ev = MagicMock()
    mock_ev.msg.datapath = mock_datapath
    simple_switch.switch_features_handler(mock_ev)
    mock_datapath.send_msg.assert_called_once()
    mock_datapath.ofproto_parser.OFPMatch.assert_called_with()
    mock_datapath.ofproto_parser.OFPActionOutput.assert_called_with(
        mock_datapath.ofproto.OFPP_CONTROLLER,
        mock_datapath.ofproto.OFPCML_NO_BUFFER
    )

def test_packet_in_handler_learns_mac(simple_switch):
    """Test that the switch learns the source MAC address of an incoming packet."""
    dpid = 1
    in_port = 1
    src_mac = "00:00:00:00:00:01"
    dst_mac = "00:00:00:00:00:02"

    mock_datapath = MagicMock(id=dpid)
    mock_datapath.ofproto = ofproto_v1_3
    mock_datapath.ofproto_parser = ofproto_v1_3_parser

    pkt = packet.Packet()
    pkt.add_protocol(ethernet.ethernet(ethertype=ether_types.ETH_TYPE_IP,
                                       dst=dst_mac,
                                       src=src_mac))
    pkt.serialize()

    mock_msg = MagicMock(datapath=mock_datapath, data=pkt.data)
    mock_msg.msg_len = len(pkt.data)
    mock_msg.total_len = len(pkt.data)
    mock_msg.match = {'in_port': in_port}
    mock_msg.buffer_id = ofproto_v1_3.OFP_NO_BUFFER
    mock_ev = ofp_event.EventOFPPacketIn(mock_msg)

    simple_switch._packet_in_handler(mock_ev)

    assert simple_switch.mac_to_port[dpid][src_mac] == in_port
    mock_datapath.send_msg.assert_called()
    sent_msg = mock_datapath.send_msg.call_args[0][0]
    assert isinstance(sent_msg, ofproto_v1_3_parser.OFPPacketOut)
    assert sent_msg.actions[0].port == ofproto_v1_3.OFPP_FLOOD
