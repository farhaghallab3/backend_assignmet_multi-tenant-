# Organization Manager App

This is my backend project.  
It is safe and fast.  
I use Python and FastAPI.

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

## How to start the app

You need Docker on your computer.

1. Run this command:
```bash
docker compose up --build