FROM alpine:latest

# Install Tor and necessary utilities
RUN apk add --no-cache tor curl 

# Create secure Tor configuration
RUN echo "# Enhanced configuration for Tor" > /etc/tor/torrc && \
    echo "SocksPort 0.0.0.0:9150" >> /etc/tor/torrc && \
    echo "DNSPort 0.0.0.0:8853" >> /etc/tor/torrc && \
    echo "DataDirectory /var/lib/tor" >> /etc/tor/torrc && \
    echo "Log notice stderr" >> /etc/tor/torrc && \
    echo "ClientOnly 1" >> /etc/tor/torrc && \
    echo "AutomapHostsOnResolve 1" >> /etc/tor/torrc && \
    echo "TransPort 0.0.0.0:9040" >> /etc/tor/torrc && \
    echo "CircuitBuildTimeout 300" >> /etc/tor/torrc && \
    echo "# Increase circuit timeout for .onion sites" >> /etc/tor/torrc && \
    echo "LearnCircuitBuildTimeout 0" >> /etc/tor/torrc && \
    echo "NumEntryGuards 8" >> /etc/tor/torrc && \
    echo "KeepalivePeriod 60" >> /etc/tor/torrc && \
    echo "NewCircuitPeriod 20" >> /etc/tor/torrc

# Create the data directory with proper permissions
RUN mkdir -p /var/lib/tor && \
    chown -R tor:tor /var/lib/tor

# Add a healthcheck script
COPY healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# Add healthcheck
HEALTHCHECK --interval=60s --timeout=15s --start-period=120s --retries=3 CMD /usr/local/bin/healthcheck.sh

# Run as the tor user
USER tor

# Launch Tor
CMD ["tor", "-f", "/etc/tor/torrc"]