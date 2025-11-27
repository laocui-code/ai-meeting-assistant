# AI Meeting Assistant

An AI-powered meeting minutes and action item management system.

## Project Overview

This project is built as part of an 18-episode tutorial series that teaches you how to build a complete AI Agent system from scratch.

### Features (by Version)

**V1 - Core Features (Episodes 1-8)**
- Meeting input and storage
- AI-generated structured meeting summaries
- Automatic action item extraction
- Action item status management
- Meeting list and detail views
- Export to Markdown/PDF

**V2 - Collaboration & Search (Episodes 9-12)**
- Participant identification and management
- Meeting classification and tagging
- Keyword and semantic search
- Advanced filtering

**V3 - External Integrations (Episodes 13-15)**
- Notion/Jira integration
- Google Calendar sync
- Post-meeting automation
- Multi-channel notifications

**V4 - Agent Capabilities (Episodes 16-18)**
- Conversational meeting queries
- Cross-meeting analysis
- Intelligent recommendations
- Agent self-reflection

## Tech Stack

- **Backend**: Python 3.10+ / FastAPI
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ORM**: SQLAlchemy 2.0
- **LLM**: Claude / GPT-4 / Qwen
- **Vector DB**: Chroma / pgvector
- **Frontend**: React 18 + TypeScript

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-meeting-assistant
   ```

2. **Set up Python virtual environment**
   ```bash
   cd backend
   python -m venv venv
   
   # Activate virtual environment
   # On Mac/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env with your API keys
   # At minimum, set your LLM API key:
   # ANTHROPIC_API_KEY=sk-ant-your-key
   # or
   # OPENAI_API_KEY=sk-your-key
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Verify installation**
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── api/                 # API routes
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── meetings.py
│   │           └── action_items.py
│   ├── core/                # Core configuration
│   │   ├── __init__.py
│   │   └── config.py
│   ├── db/                  # Database configuration
│   │   ├── __init__.py
│   │   └── database.py
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── meeting.py
│   │   └── action_item.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── meeting.py
│   │   └── action_item.py
│   └── services/            # Business logic
│       └── __init__.py
├── requirements.txt
├── env.example
└── .gitignore

frontend/                    # React frontend (added later)
└── ...
```

## API Endpoints

### Health Check
- `GET /health` - Application health status
- `GET /` - Welcome message with API links

### Meetings (v1)
- `GET /api/v1/meetings` - List all meetings
- `POST /api/v1/meetings` - Create a new meeting
- `GET /api/v1/meetings/{id}` - Get meeting details
- `DELETE /api/v1/meetings/{id}` - Delete a meeting

### Action Items (v1)
- `GET /api/v1/action-items` - List action items
- `POST /api/v1/action-items` - Create action item
- `GET /api/v1/action-items/{id}` - Get action item
- `PUT /api/v1/action-items/{id}` - Update action item
- `PATCH /api/v1/action-items/{id}/status` - Update status
- `DELETE /api/v1/action-items/{id}` - Delete action item

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
# Format code
black app/

# Sort imports
isort app/

# Type checking
mypy app/
```

### Database Migrations (with Alembic)
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Episode Guide

| Episode | Topic | Key Deliverables |
|---------|-------|------------------|
| E01 | Project Overview & Tech Stack | Project scaffold, environment setup |
| E02 | FastAPI & Database Design | Complete backend structure, ORM models |
| E03 | Meeting Input & Summary Generation | LLM integration, Prompt engineering |
| E04 | Action Item Extraction | NER, date extraction, priority |
| E05 | Action Item Management | CRUD operations, status workflow |
| E06 | Meeting List Frontend | React setup, API integration |
| E07 | Meeting Detail Page | Three-column layout |
| E08 | Summary Enhancement & Export | Editing, PDF/Markdown export |
| E09 | Participant Management | Auto-identification, statistics |
| E10 | Vector Storage & Keyword Search | Chroma/pgvector setup |
| E11 | Semantic Search | Vector similarity, hybrid search |
| E12 | Advanced Filtering | Multi-filter UI, search page |
| E13 | Task System Integration | Notion/Jira sync |
| E14 | Calendar Integration | Google Calendar, automation |
| E15 | Notifications & Agent Intro | Multi-channel, tool calling |
| E16 | Conversational Query | Chat interface, memory |
| E17 | Cross-Meeting Analysis | RAG, conflict detection |
| E18 | Trends & Recommendations | Analytics, self-reflection |

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Support

For questions or issues, please open a GitHub issue or leave a comment on the tutorial videos.

