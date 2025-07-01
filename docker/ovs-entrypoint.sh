#!/bin/bash
set -e

# Ensure the OVS run and config directories exist
mkdir -p /var/run/openvswitch
mkdir -p /etc/openvswitch

DB_FILE="/etc/openvswitch/conf.db"

# Create the OVS database if it doesn't exist
if [ ! -e "$DB_FILE" ]; then
    ovsdb-tool create "$DB_FILE" /usr/share/openvswitch/vswitch.ovsschema
fi

# Start OVS services, providing the database file as the main argument
ovsdb-server "$DB_FILE" --remote=punix:/var/run/openvswitch/db.sock --pidfile --detach
ovs-vswitchd --pidfile --detach

# Execute the command passed to the container
exec "$@"

