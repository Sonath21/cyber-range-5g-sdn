SHELL  := /bin/bash
PYTHON := $(abspath playground/.venv/bin/python)

.PHONY: up down scan capture split clean

# ── network stack ────────────────────────────────────────────────────────────
# Bring up victim + db **only** (leave scanner to be launched ad-hoc)
up:
	docker compose up -d victim db

down:
	docker compose down

# ── manual scan (idempotent) ────────────────────────────────────────────────
scan:
	docker compose run --rm scanner

# ── capture 10 s on the lab bridge ──────────────────────────────────────────
# Runs `make up` first to be sure the network exists,
# launches a one-shot scanner container, then captures traffic.
capture: up
	@echo "Detecting lab bridge …"
	@NET_ID=$$(docker network inspect cyber-range-5g-sdn_lab_net -f '{{.Id}}'); \
	BR=br-$${NET_ID:0:12}; \
	echo "Launching scanner container …"; \
	docker compose run -d --name temp_scanner scanner >/dev/null; \
	echo "Capturing on $$BR for 10 s …"; \
	tshark -i $$BR -w host_capture.pcap -a duration:10; \
	echo "Stopping scanner …"; \
	docker stop temp_scanner >/dev/null; \
	docker rm   temp_scanner >/dev/null

# ── split capture into per-flow pcaps ───────────────────────────────────────
split:
	$(PYTHON) playground/pcap_splitter.py host_capture.pcap out_flows_host/

# ── tidy scratch artefacts ──────────────────────────────────────────────────
clean:
	rm -rf host_capture.pcap out_flows_host/

