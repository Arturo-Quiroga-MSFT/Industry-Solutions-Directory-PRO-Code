# Dockerfile for MCP ISD Server
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for HTTP server
RUN pip install --no-cache-dir uvicorn fastapi mcp[server]

# Copy application code
COPY server.py .
COPY http_server.py .

# Expose port for HTTP endpoint
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run HTTP server (not stdio)
CMD ["uvicorn", "http_server:app", "--host", "0.0.0.0", "--port", "8080"]
