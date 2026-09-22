FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Install deps first so code changes don't bust the layer cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY main.py schemas.py database.py storage.py errors.py dashboard.py dashboard.html worker.py ./

ENV PATH="/app/.venv/bin:$PATH" \
    RELAY_DATABASE_URL="sqlite:///./agent-relay.db"

EXPOSE 8000
# --host 0.0.0.0: uvicorn defaults to 127.0.0.1, which is unreachable from
# outside the container and makes `docker run -p` look broken.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
