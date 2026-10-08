from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from pwdlib import PasswordHash
import sqlite3
import hashlib
import secrets
import time

from database import (
    get_connection,
    initialize_database,
    add_password_column,
    initialize_login_sessions,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    add_password_column()
    initialize_login_sessions()
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
    allow_headers=["Content-Type", "Authorization"],
)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_student(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    unauthorized = HTTPException(
        status_code=401,
        detail="Please log in again",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    token_hash = hashlib.sha256(
        credentials.credentials.encode()
    ).hexdigest()

    with get_connection() as connection:
        student = connection.execute(
            """
            SELECT s.id, s.name, s.email
            FROM login_sessions AS ls
            JOIN students AS s ON s.id = ls.student_id
            WHERE ls.token_hash = ? AND ls.expires_at > ?
            """,
            (token_hash, int(time.time())),
        ).fetchone()

    if student is None:
        raise unauthorized

    return dict(student)


@app.get("/auth/me")
def get_my_profile(student: dict = Depends(get_current_student)):
    return student

class SessionCreate(BaseModel):
    course: str = Field(min_length=1, max_length=30)
    topic: str = Field(min_length=1, max_length=150)
    location: str = Field(min_length=1, max_length=150)
    max_participants: int = Field(gt=0, le=50)


@app.get("/")
def home():
    return {"message": "Study Group Finder API is running"}




@app.get("/sessions")
def get_sessions(student: dict = Depends(get_current_student)):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT s.*,
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
            (student["id"],),
        ).fetchall()

    sessions = []
    for row in rows:
        session = dict(row)
        session["joined"] = bool(session["joined"])
        sessions.append(session)

    return sessions


@app.post("/sessions", status_code=201)
def create_session(
    session: SessionCreate,
    student: dict = Depends(get_current_student),
):
    
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


@app.post("/sessions/{session_id}/join", status_code=201)
def join_session(
    session_id: int,
    student: dict = Depends(get_current_student),
):
    student_id = student["id"]

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        session = connection.execute(
            "SELECT * FROM study_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Study group not found",
            )

        existing = connection.execute(
            """
            SELECT 1 FROM memberships
            WHERE student_id = ? AND session_id = ?
            """,
            (student_id, session_id),
        ).fetchone()

        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="You have already joined this group",
            )

        count = connection.execute(
            "SELECT COUNT(*) FROM memberships WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]

        if count >= session["max_participants"]:
            raise HTTPException(
                status_code=409,
                detail="This study group is full",
            )

        connection.execute(
            """
            INSERT INTO memberships (student_id, session_id)
            VALUES (?, ?)
            """,
            (student_id, session_id),
        )

    return {
        "message": "Joined study group successfully",
        "session_id": session_id,
        "student_id": student_id,
    }
@app.post("/sessions/{session_id}/leave")
def leave_session(
    session_id: int,
    student: dict = Depends(get_current_student),
):
    student_id = student["id"]

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM memberships
            WHERE student_id = ? AND session_id = ?
            """,
            (student_id, session_id),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="You are not a member of this group",
            )

    return {
        "message": "Left study group successfully",
        "session_id": session_id,
        "student_id": student_id,
    }
password_hasher = PasswordHash.recommended()


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


@app.post("/auth/register", status_code=201)
def register_student(student: RegisterRequest):
    name = student.name.strip()
    email = str(student.email).lower()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name cannot be blank"
        )

    password_hash = password_hasher.hash(student.password)

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO students (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (name, email, password_hash)
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
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


@app.post("/auth/login")
def login_student(credentials: LoginRequest):
    email = str(credentials.email).lower()

    with get_connection() as connection:
        student = connection.execute(
            "SELECT * FROM students WHERE email = ?",
            (email,),
        ).fetchone()

    if student is None or not student["password_hash"]:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    if not password_hasher.verify(
        credentials.password, student["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = int(time.time()) + 3600

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO login_sessions
                (token_hash, student_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token_hash, student["id"], expires_at),
        )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600,
        "student": {
            "id": student["id"],
            "name": student["name"],
            "email": student["email"],
        },
    }

@app.post("/auth/logout")
def logout_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    student: dict = Depends(get_current_student),
):
    token_hash = hashlib.sha256(
        credentials.credentials.encode()
    ).hexdigest()

    with get_connection() as connection:
        connection.execute(
            "DELETE FROM login_sessions WHERE token_hash = ?",
            (token_hash,),
        )

    return {"message": "Logged out successfully"}
