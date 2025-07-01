from pathlib import Path
import pyshark
from playground import pcap_splitter


SAMPLES = Path(__file__).resolve().parent.parent / "samples"
TMPDIR = Path(__file__).resolve().parent / "_tmp_split"


def test_splitter_creates_expected_files(tmp_path):
    in_pcap = SAMPLES / "dns_port.pcap"
    pcap_splitter.split_pcap(in_pcap, tmp_path)

    files = sorted(p.name for p in tmp_path.iterdir())
    assert len(list(tmp_path.iterdir())) >= 1  # at least one flow file extracted
    assert all(
        name.endswith(".pcap") for name in files
    )  # Spot-check one expected filename pattern

    # Tiny sanity check: open first child and make sure it has packets
    child = tmp_path / files[0]
    cap = pyshark.FileCapture(str(child))
    pkt_count = sum(1 for _ in cap)
    assert pkt_count > 0
    cap.close()
