# AATES Platform Development Guide

## Local Quickstart

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL & Redis (optional, local SQLite configured for tests)

### Backend Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables (or copy `.env.example` if created):
   ```bash
   # Create a local .env file
   APP__ENV=development
   DB__URL=sqlite:///./test.db
   REDIS__URL=redis://localhost:6379/0
   ```
3. Run migrations:
   ```bash
   alembic upgrade head
   ```
4. Start FastAPI server:
   ```bash
   uvicorn apps.api.main:app --reload --port 8000
   ```

### Frontend Setup
1. Install dependencies:
   ```bash
   cd apps/dashboard
   npm install
   ```
2. Start Next.js development server:
   ```bash
   npm run dev
   ```

## Test Verification
To run the automated API and authentication test suites:
```bash
python -m pytest tests/
```

## Git Branching Strategy
We enforce the following branch rules:
- `main`: stable production-ready code.
- `develop`: active feature integration branch.
- `feature/*`: temporary branches created for individual tasks.
- `release/*`: preparation branches for QA testing before main merging.
- `hotfix/*`: emergency production patches.

### Branch Protection Recommendations
- Require pull request reviews before merging.
- Require status checks (GitHub Actions CI) to pass before merging.
- Dismiss stale pull request approvals when new commits are pushed.
