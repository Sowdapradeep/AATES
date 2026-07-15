# AATES Dependencies Documentation

This guide describes the platform runtime packages and library requirements.

## 1. Backend Python Dependencies
Defined in `requirements.txt`:

*   **FastAPI & Uvicorn**: ASGI web server engine and router execution layer.
*   **SQLAlchemy & Alembic**: Database ORM model declarations and schema migration configurations.
*   **Pydantic & Pydantic-Settings**: Data validation serialization and environment variables parsing.
*   **Bcrypt**: Native cryptographically secure password hashing.
*   **python-jose**: JWT signature encoding and cookie parsing.
*   **python-json-logger**: Structured JSON format logging adapter.
*   **APScheduler**: Scheduler task trigger loop management.
*   **PyYAML**: External prompts file reader and version tracker parsing.

---

## 2. Frontend NPM Dependencies
Defined in `apps/dashboard/package.json`:

*   **Next.js (v14/15+)**: React client App Router rendering layout framework.
*   **React & React-DOM**: Component states rendering engine.
*   **Tailwind CSS (v4)**: Modern utility style sheets framework.
*   **TypeScript**: Static type safety checks verification.
*   **lucide-react**: Premium system map, logs terminal, and control panel UI icons.
