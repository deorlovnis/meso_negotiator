FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY back/ back/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "back.server:app", "--host", "0.0.0.0", "--port", "8000"]

