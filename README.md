# Organization Manager App

This is my backend project  
I use Python and FastAPI

## Database Design

The system uses a relational schema optimized for multi-tenancy and high-performance search.

```mermaid
erDiagram
    USER ||--o{ MEMBERSHIP : has
    ORGANIZATION ||--o{ MEMBERSHIP : contains
    ORGANIZATION ||--o{ ITEM : owns
    ORGANIZATION ||--o{ AUDIT_LOG : records
    USER ||--o{ ITEM : creates
    USER ||--o{ AUDIT_LOG : performs

    USER {
        int id PK
        string email UK
        string hashed_password
        string full_name
        tsvector search_vector
        datetime created_at
    }
    ORGANIZATION {
        int id PK
        string name
        datetime created_at
    }
    MEMBERSHIP {
        int id PK
        int user_id FK
        int org_id FK
        enum role
        datetime created_at
    }
    ITEM {
        int id PK
        jsonb item_details
        int org_id FK
        int user_id FK
        datetime created_at
    }
    AUDIT_LOG {
        int id PK
        string action
        text details
        int org_id FK
        int user_id FK
        datetime created_at
    }
```


- **User**: Stores global account information. Features a `TSVECTOR` column (`search_vector`) with a `GIN` index for ultra-fast full-text search across names and emails.
- **Organization**: The tenant boundary. All business data (Items) and logs belong to an organization.
- **Membership**: A standard junction table with an added `role` column (`admin` or `member`) to enforce RBAC.
- **Item**: Flexible data storage using PostgreSQL `JSONB` for schema-less business logic support while maintaining relational integrity.
- **AuditLog**: An append-only table used for security tracking and as the data source for the AI Chatbot's daily summaries.

## What the app can do
- Users can sign up and log in (with JWT)
- Create organizations
- Invite people (Admin or Member)
- Add items (only see your items if Member)
- Admin see all items
- Search users fast (with Postgres full-text)
- See activity logs
- Ask AI questions about logs (use Google Gemini)
- Everything is async

## Technologies I use
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL
- JWT for login
- Docker + Docker Compose
- Google Gemini 
- Pytest + Testcontainers for tests

## AI Chatbot 

The AI part uses Google Gemini

How to use real AI:
1. Go → https://aistudio.google.com/app/apikey
2. Make new key (free)
3. Copy .env
4. Write your key: GEMINI_API_KEY=AIz...
5. Run docker compose up --build

## How to start the app

You need Docker on your computer.

1. Run this command:
```bash
docker compose up --build