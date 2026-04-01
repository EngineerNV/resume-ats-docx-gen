FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && pip install .

RUN mkdir -p /app/outbox

EXPOSE 8765

ENV RESUME_MCP_TRANSPORT=sse \
    RESUME_MCP_HOST=0.0.0.0 \
    RESUME_MCP_PORT=8765

CMD ["python", "-m", "resume_mcp.server"]
