# AI Meeting Assistant - Backend

The backend service for AI Meeting Assistant, built with FastAPI and SQLAlchemy 2.0.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point with lifespan management
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py  # API v1 router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── meetings.py      # Meeting endpoints (E03)
│   │           └── action_items.py  # Action item endpoints (E04-E05)
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Application configuration
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py      # Database connection and session management
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── meeting.py       # Meeting model
│   │   └── action_item.py   # ActionItem model with enums
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── meeting.py       # Meeting schemas
│   │   └── action_item.py   # ActionItem schemas
│   └── services/            # Business logic (E03+)
│       └── __init__.py
├── requirements.txt
├── env.example              # Environment variables template
└── README.md
```

## Implementation Status

| Episode | Content | Status |
|---------|---------|--------|
| E01 | Project setup & environment | Done |
| E02 | FastAPI service & database models | Done |
| E03 | Meeting CRUD & LLM integration | Pending |
| E04 | Action item extraction | Pending |
| E05 | Action item management | Pending |

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env with your settings (especially LLM_API_KEY for E03+)
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload
```

### 4. Verify

- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database

The application uses SQLite for development (automatically created as `meeting_assistant.db`).

### Tables

- `meetings`: Stores meeting records with title, content, summary, and status
- `action_items`: Stores action items with foreign key to meetings

### Models

**Meeting**
- id, title, start_time, end_time
- original_text, summary
- status (draft/processing/completed)
- created_at, updated_at

**ActionItem**
- id, meeting_id (FK)
- title, description, owner, due_date
- status (todo/in_progress/done/cancelled)
- priority (high/medium/low)
- created_at, updated_at

## API Endpoints

### System
- `GET /` - Welcome message and links
- `GET /health` - Health check with timestamp

### Meetings (E03)
- `GET /api/v1/meetings` - List meetings
- `POST /api/v1/meetings` - Create meeting
- `GET /api/v1/meetings/{id}` - Get meeting
- `PUT /api/v1/meetings/{id}` - Update meeting
- `DELETE /api/v1/meetings/{id}` - Delete meeting
- `POST /api/v1/meetings/{id}/generate-summary` - Generate AI summary

### Action Items (E04-E05)
- `GET /api/v1/action-items` - List action items
- `POST /api/v1/action-items` - Create action item
- `GET /api/v1/action-items/{id}` - Get action item
- `PUT /api/v1/action-items/{id}` - Update action item
- `PATCH /api/v1/action-items/{id}/status` - Update status
- `DELETE /api/v1/action-items/{id}` - Delete action item

## Technology Stack

- **Framework**: FastAPI 0.115.6
- **ORM**: SQLAlchemy 2.0.36 (async)
- **Validation**: Pydantic 2.10.3
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Async Driver**: aiosqlite

## License

MIT License

