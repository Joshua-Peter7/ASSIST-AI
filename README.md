# Real-Time AI Suggestion System

FastAPI backend for document ingestion, cached RAG retrieval, Soniox transcript intake, deterministic sub-100ms suggestion serving, and asynchronous post-call compliance reporting.

## What It Includes

- Document ingestion for PDF, DOCX, and TXT with chunking, metadata tagging, embeddings, and vector upsert.
- Session start flow that pre-fetches RAG context into Redis before the call begins.
- Transcript ingestion endpoint for Soniox text chunks with buffer storage and rule-based signal extraction.
- Real-time suggestion engine that defaults to deterministic logic and uses an LLM only when refinement is explicitly needed.
- Background compliance reporting via Celery with structured report persistence in SQLite.

## Quick Start

1. Copy `.env.example` to `.env` and fill in the LLM keys you want to use.
2. Start the stack with `docker compose up --build`.
3. Open `http://localhost:8000/docs` for the API docs.

## Key Performance Design

- The real-time path does not call the vector DB mid-call.
- `POST /session/start` preloads the RAG cache using metadata filters and a seed query.
- `POST /transcript` updates the transcript buffer, signal state, and latest suggestion in Redis.
- `GET /suggestion` returns the latest cached suggestion and stays lightweight for the happy path.

## Main Endpoints

- `POST /ingest`
- `POST /session/start`
- `POST /transcript`
- `GET /suggestion?session_id=...`
- `POST /session/end`
- `GET /report/{session_id}`

## Testing

Run `pytest` from the project root.

## Notes

- `LLM_PROVIDER=noop` keeps the system fully local for development and tests.
- `EMBEDDING_PROVIDER=hash` provides deterministic embeddings without external APIs.
- Swap in a production LLM or embedding provider through environment configuration without changing business logic.
