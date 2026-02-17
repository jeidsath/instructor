# Instructor

AI-powered language instruction system for Ancient Greek and Latin. Models a learner's knowledge and capacities, then evaluates, teaches, and practices to develop reading, writing, listening, and speaking skills.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Node.js 22+](https://nodejs.org/) and [pnpm](https://pnpm.io/)
- [Task](https://taskfile.dev/installation/) (task runner)

## Getting Started

```bash
# Copy environment template and add your Anthropic API key
cp .env.example .env

# Start the backend (FastAPI + PostgreSQL)
task dev

# In another terminal, install and start the frontend
task frontend:install
task frontend:dev
```

This brings up:
- React frontend at **http://localhost:5173** (proxies `/api` to the backend)
- FastAPI app at **http://localhost:8000** (hot-reload via volume mount)
- PostgreSQL 16 at **localhost:5432**

```bash
# Run database migrations
task db:migrate

# Stop everything
task dev:down
```

## Running Tests

```bash
# Everything (Python lint, typecheck, tests + frontend lint, typecheck, tests, build)
task check

# Backend only
task test              # all Python tests (unit + integration)
task test:unit         # unit tests only — no database needed
task test:integration  # spins up a test DB, runs integration tests, stops DB
task test:cov          # all tests with coverage report

# Frontend only
task frontend:check    # lint + typecheck + test + build
task frontend:test     # Vitest only
task frontend:lint     # ESLint only
task frontend:typecheck # tsc --noEmit only
```

## Code Quality

```bash
task lint              # Ruff linter
task format            # Ruff formatter
task typecheck         # mypy
task ci                # mirror the GitHub Actions pipeline in Docker
```

## Other Commands

```bash
task dev:rebuild       # rebuild app container after dependency changes
task db:reset          # drop and recreate the dev database
task frontend:dev      # start frontend dev server
task frontend:build    # production build to frontend/dist/
```

## Production Build

The Dockerfile builds both frontend and backend into a single image. FastAPI serves the built frontend and handles SPA routing:

```bash
docker-compose up --build
# App available at http://localhost:8000
```

## Project Structure

```
src/instructor/        # Python backend (FastAPI)
  api/                 # Routes and Pydantic schemas
  models/              # SQLAlchemy models
  learner/             # Learner model, spaced repetition, mastery, capacity
  curriculum/          # YAML schemas, loader, registry
  evaluator/           # Rule-based scoring, placement assessment
  practice/            # Exercise generation, adaptive selection
  instructor_engine/   # Lesson orchestration, AI content generation
  session/             # Session manager
  nlp/                 # Morphological analysis, lemmatization
  ai/                  # Anthropic client, prompts, AI evaluation
src/tests/             # pytest suite (unit + integration)
curriculum/            # YAML data files (greek/ and latin/)
alembic/               # Database migrations
frontend/              # React SPA (Vite + TypeScript + Tailwind CSS)
  src/api/             # Typed API client layer
  src/components/      # Shared UI components
  src/context/         # React Context (learner identity)
  src/pages/           # Route pages (landing, register, dashboard, practice,
                       #   placement, progress)
```
