FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ .
RUN pnpm build

FROM python:3.12-slim AS builder

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid 1000 --create-home app

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

USER app

EXPOSE 8000

CMD ["uvicorn", "instructor.main:app", "--host", "0.0.0.0", "--port", "8000"]
