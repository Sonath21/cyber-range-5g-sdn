#!/bin/sh
set -e

# Wait for OVS daemons to be ready
while ! ovs-vsctl show > /dev/null 2>&1; do
  echo "Waiting for OVS to be ready..."
  sleep 1
done

echo "OVS is ready. Configuring bridge br-int..."

# Setup the bridge and controller
ovs-vsctl --may-exist add-br br-int
ovs-vsctl set-controller br-int tcp:ryu-controller:6633
ovs-vsctl set bridge br-int protocols=OpenFlow13
ovs-vsctl set-fail-mode br-int secure

# Add ports for the hosts
ovs-vsctl --may-exist add-port br-int eth1
ovs-vsctl --may-exist add-port br-int eth2

echo "Bridge br-int configured successfully."

# Keep the container running
tail -f /dev/null
