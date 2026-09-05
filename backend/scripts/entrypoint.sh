#!/bin/sh
set -e

cd /app

# Compose supplies the API, migration, or worker command. exec preserves
# signals so containers shut down cleanly.
exec "$@"
