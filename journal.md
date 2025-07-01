# Cyber-Range 5 G / SDN — Lab Journal
*A running record of everything built, tested, and learned.*

---

## Python Toolchain (Session 1-2)

* **Virtual-env**: `python -m venv .venv` in `playground/`  
* Installed & pinned dev-deps: `black`, `ruff`, `pre-commit`, `pytest`, `pytest-mock`.  
* Set up **pre-commit hooks**  
  * `black` auto-formats  
  * `ruff` lints with auto-fix  
* Repo structure:

```bash
cyber-range-5g-sdn/
├── playground/              # active code
├── tests/                   # pytest suites
├── samples/                 # tiny pcaps
└── .pre-commit-config.yaml  # pre-commit hooks config
```

---

## Port Scanner v1 (Session 3)

* `playground/port_scanner.py`  
  * ThreadPool backend (`--mode thread`)  
  * Unit tests for target expansion + socket mocks.  
* Green `pytest` + pre-commit pipeline.


## Port Scanner v2 (Concurrency Deep-Dive)

* Added **`--mode asyncio`** and **`--mode process`** back-ends.  
* Added `--benchmark` flag → logs runtime for easy perf tests.  
* Tests updated with `pytest-asyncio`.  
* Learned: `asyncio` ~2× faster for 1 k+ sockets.

---

## Pcap Splitter (Session 4)

* `playground/pcap_splitter.py`  
  * Reads capture via PyShark (`include_raw + use_json`).  
  * Writes per-flow pcaps via **Scapy PcapWriter** (link-type 1).  
* Sample `dns_port.pcap` placed in `samples/`.  
* Tests create temp dir, assert ≥ 1 flow file, open a child pcap to ensure packets exist.

---

## Docker Networking Lab (Session 5)

### Compose stack (`docker-compose.yml`)

| Service  | Purpose | IP (lab_net) |
|----------|---------|--------------|
| `victim` | **nginx:alpine** web server | 172.19.0.10 |
| `db`     | **postgres:16-alpine**     | 172.19.0.11 |
| `scanner`| Image built from repo; runs `port_scanner.py` | 172.19.0.50 |

* Network: `cyber-range-5g-sdn_lab_net` → bridge `br-ae5a817dbeb8`.
* **Automated Makefile**:  
  - `make up` → starts services  
  - `make capture` → runs scanner + captures 10 s on bridge  
  - `make split` → splits `host_capture.pcap` into per-flow pcaps  
  - `make down` → tears down  
* **Captures & Datasets**:  
  - HTTP flows → `datasets/benign_http` + `meta.json`  
  - Postgres flows → `datasets/benign_postgres` + `meta.json`  


### `Dockerfile.scanner`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY playground playground
CMD ["python", "playground/port_scanner.py", "--help"]



