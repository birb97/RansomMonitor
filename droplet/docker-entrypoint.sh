#!/bin/bash
set -e

# Print what server we're using
echo "Starting collection agent using production WSGI server (Gunicorn)"

# Start with Gunicorn
exec gunicorn --bind 0.0.0.0:5000 --workers 4 collection_agent:app