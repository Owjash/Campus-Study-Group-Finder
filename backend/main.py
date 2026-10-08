from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3

from database import get_connection, initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Campus Study Group Finder",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class SessionCreate(BaseModel):
    course: str = Field(min_length=1, max_length=30)
    topic: str = Field(min_length=1, max_length=150)
    location: str = Field(min_length=1, max_length=150)
    max_participants: int = Field(gt=0, le=50)


@app.get("/")
def home():
    return {"message": "Study Group Finder API is running"}




@app.get("/sessions")
def get_sessions(student_id: int | None = None):
    with get_connection() as connection:
        if student_id is not None:
            student = connection.execute(
                "SELECT id FROM students WHERE id = ?",
                (student_id,)
            ).fetchone()

            if student is None:
                raise HTTPException(
                    status_code=404,
                    detail="Student not found"
                )

        rows = connection.execute(
            """
            SELECT
                s.*,
                (
                    SELECT COUNT(*)
                    FROM memberships AS m
                    WHERE m.session_id = s.id
                ) AS participant_count,
                EXISTS (
                    SELECT 1
                    FROM memberships AS m
                    WHERE m.session_id = s.id
                      AND m.student_id = ?
                ) AS joined
            FROM study_sessions AS s
            ORDER BY s.id
            """,
            (student_id,)
        ).fetchall()

        sessions = []

        for row in rows:
            session = dict(row)
            session["joined"] = bool(session["joined"])
            sessions.append(session)

        return sessions


@app.post("/sessions", status_code=201)
def create_session(session: SessionCreate):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO study_sessions
                (course, topic, location, max_participants)
            VALUES (?, ?, ?, ?)
            """,
            (
                session.course,
                session.topic,
                session.location,
                session.max_participants
            )
        )

        new_session = session.model_dump()
        new_session["id"] = cursor.lastrowid

    return new_session
class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=150)


@app.post("/students", status_code=201)
def create_student(student: StudentCreate):
    name = student.name.strip()
    email = student.email.strip().lower()

    if not name or not email:
        raise HTTPException(
            status_code=400,
            detail="Name and email cannot be empty"
        )

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO students (name, email) VALUES (?, ?)",
                (name, email)
            )

            student_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="This email is already registered"
        )

    return {
        "id": student_id,
        "name": name,
        "email": email
    }

class MembershipCreate(BaseModel):
    student_id: int = Field(gt=0)

@app.post("/sessions/{session_id}/join", status_code=201)
def join_session(session_id: int, membership: MembershipCreate):
    with get_connection() as connection:
        # Allow only one writer during the capacity check and insert.
        connection.execute("BEGIN IMMEDIATE")

        session = connection.execute(
            "SELECT * FROM study_sessions WHERE id = ?",
            (session_id,)
        ).fetchone()

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Study group not found"
            )

        student = connection.execute(
            "SELECT id FROM students WHERE id = ?",
            (membership.student_id,)
        ).fetchone()

        if student is None:
            raise HTTPException(
                status_code=404,
                detail="Student not found"
            )

        existing = connection.execute(
            """
            SELECT 1 FROM memberships
            WHERE student_id = ? AND session_id = ?
            """,
            (membership.student_id, session_id)
        ).fetchone()

        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="Student has already joined this group"
            )

        count = connection.execute(
            "SELECT COUNT(*) FROM memberships WHERE session_id = ?",
            (session_id,)
        ).fetchone()[0]

        if count >= session["max_participants"]:
            raise HTTPException(
                status_code=409,
                detail="This study group is full"
            )

        connection.execute(
            """
            INSERT INTO memberships (student_id, session_id)
            VALUES (?, ?)
            """,
            (membership.student_id, session_id)
        )

    return {
        "message": "Joined study group successfully",
        "session_id": session_id,
        "student_id": membership.student_id
    }
@app.post("/sessions/{session_id}/leave")
def leave_session(session_id: int, membership: MembershipCreate):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM memberships
            WHERE student_id = ? AND session_id = ?
            """,
            (membership.student_id, session_id)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Student is not a member of this group"
            )

    return {
        "message": "Left study group successfully",
        "session_id": session_id,
        "student_id": membership.student_id
    }
