FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WIPO_HEADLESS=1 \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

WORKDIR /app

# Chromium + driver are required for Selenium-based WIPO automation.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
COPY schemas /app/schemas
COPY runtime /app/runtime
COPY run_stdio.sh /app/run_stdio.sh
COPY run_http.sh /app/run_http.sh

RUN chmod +x /app/run_stdio.sh /app/run_http.sh
RUN pip install --upgrade pip && pip install -e /app

EXPOSE 8000

CMD ["/app/run_http.sh"]
