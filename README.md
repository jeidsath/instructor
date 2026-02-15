# Instructor

AI-powered language instruction system for Ancient Greek and Latin. Models a learner's knowledge and capacities, then evaluates, teaches, and practices to develop reading and comprehension skills.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Task](https://taskfile.dev/installation/) (task runner)

## Getting Started

```bash
# Copy environment template and add your Anthropic API key
cp .env.example .env

# Start the app and database
task dev
```

This brings up:
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
task test              # all tests (unit + integration)
task test:unit         # unit tests only — no database needed
task test:integration  # spins up a test DB, runs integration tests, stops DB
task test:cov          # all tests with coverage report
```

## Code Quality

```bash
task lint              # Ruff linter
task format            # Ruff formatter
task typecheck         # mypy
task check             # lint + typecheck + tests (full local CI)
task ci                # mirror the GitHub Actions pipeline in Docker
```

## Other Commands

```bash
task dev:rebuild       # rebuild app container after dependency changes
task db:reset          # drop and recreate the dev database
```

## Project Structure

```
src/instructor/        # application source
  models/              # SQLAlchemy models
  learner/             # learner model, spaced repetition, mastery, capacity
  curriculum/          # YAML schemas, loader, registry
  evaluator/           # rule-based scoring, placement assessment
  practice/            # exercise generation, adaptive selection
  instructor_engine/   # lesson orchestration, AI content generation
  session/             # session manager
  nlp/                 # morphological analysis, lemmatization
  ai/                  # Anthropic client, prompts, AI evaluation
  api/                 # FastAPI routes and Pydantic schemas
src/tests/             # pytest suite (unit + integration)
curriculum/            # YAML data files (greek/ and latin/)
alembic/               # database migrations
```
