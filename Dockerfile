FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (sqlite3, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir .

# Create volume mount points
VOLUME ["/app/data"]

# Default entrypoint (can be overridden)
ENTRYPOINT ["kirosu"]
CMD ["hub", "--host", "0.0.0.0", "--port", "8765", "--db", "/app/data/swarm.db"]
