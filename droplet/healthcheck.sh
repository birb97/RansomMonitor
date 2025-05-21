#!/bin/sh
# Health check script for Tor container

# Check if SOCKS proxy is running
if ! nc -z 127.0.0.1 9150; then
  echo "Tor SOCKS proxy not running"
  exit 1
fi

# Try to connect to check.torproject.org
if ! curl --socks5-hostname 127.0.0.1:9150 -s https://check.torproject.org | grep -q 'Congratulations'; then
  echo "Tor not working correctly"
  exit 1
fi

echo "Tor is healthy"
exit 0