FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install flask requests pysocks gunicorn

# Copy your agent code and entrypoint script
COPY collection_agent.py /app/
COPY docker-entrypoint.sh /app/

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose the port
EXPOSE 5000

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]