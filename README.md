# Campus Study Group Finder

A full-stack application that helps students find classmates and form study groups.

## Features

- Register an account, log in, and log out
- Create study groups with a course, topic, location, and capacity
- Search groups by course or topic
- Join and leave groups
- Filter the list to show your joined groups
- Prevent duplicate memberships and joins when a group is full
- Save accounts, groups, and memberships in SQLite

## Technologies

- Frontend: React, JavaScript, HTML, CSS, Vite
- Backend: Python, FastAPI, Pydantic
- Database: SQLite and SQL
- Authentication: Argon2 password hashing and expiring bearer tokens

## How It Works

React sends HTTP requests to the FastAPI backend. FastAPI validates the
requests and reads or writes data in SQLite.

Protected requests include a bearer token. The backend uses that token
to identify the student. Logout invalidates the token's session.

## Run Locally

Developed using Python 3.14 and Node.js 24.

### Backend

From the project folder:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install fastapi uvicorn "pwdlib[argon2]" "pydantic[email]"
python -m uvicorn main:app --reload
```

The database is created automatically when the backend starts.

API documentation: http://127.0.0.1:8000/docs

### Frontend

Open a second terminal in the project folder:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173 and create an account to begin.

Keep both servers running while using the application.

## Data Model

- `students`: account details and password hashes
- `study_sessions`: study group details and capacity
- `memberships`: links students to groups
- `login_sessions`: hashed login tokens and expiry times

## Current Limitations

- Login tokens expire after one hour.
- Refreshing the frontend requires logging in again.
- Meeting scheduling and group editing are not implemented.
- This is a local portfolio project; production deployment and automated
  tests are future work.

## Author
Owjash Acharya