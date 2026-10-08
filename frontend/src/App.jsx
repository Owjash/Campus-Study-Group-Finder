import { useEffect, useState } from "react";
import "./App.css";
import CreateSession from "./CreateSession";
import GroupMembership from "./GroupMembership";
import Login from "./Login";
import Register from "./Register";


function App() {
  const [auth, setAuth] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [onlyJoined, setOnlyJoined] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [notice, setNotice] = useState("");
  const token = auth?.access_token;

  useEffect(() => {
    if (!token) {
      return;
    }

    let ignore = false;
    setLoading(true);
    setError("");

    async function loadSessions() {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/sessions",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.status === 401) {
          if (!ignore) {
            setAuth(null);
            setSessions([]);
          }
          throw new Error("Your login expired. Please log in again.");
        }

        if (!response.ok) {
          throw new Error("Could not load study groups.");
        }

        const data = await response.json();

        if (!ignore) {
          setSessions(data);
        }
      } catch (err) {
        if (!ignore) {
          setError(err.message);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadSessions();

    return () => {
      ignore = true;
    };
  }, [token]);


  async function handleLogout() {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/auth/logout",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok && response.status !== 401) {
      throw new Error("Could not log out. Please try again.");
    }

    setAuth(null);
    setSessions([]);
    setError("");
  } catch (err) {
    setError(err.message);
  }
}

  function handleLogin(result) {
    setError("");
    setSessions([]);
    setSearch("");
    setOnlyJoined(false);
    setAuth(result);
  }

  const query = search.trim().toLowerCase();

  const filteredSessions = sessions.filter((session) => {
    const matchesSearch =
      session.course.toLowerCase().includes(query) ||
      session.topic.toLowerCase().includes(query);

    return matchesSearch && (!onlyJoined || session.joined);
  });

  if (!auth) {
  return (
    <main className="page">
      <h1>Campus Study Group Finder</h1>

      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}

      {showRegister ? (
        <Register
          onRegistered={() => {
            setShowRegister(false);
            setError("");
            setNotice("Account created! You can now log in.");
          }}
        />
      ) : (
        <Login onLogin={handleLogin} />
      )}

      <button
        type="button"
        onClick={() => {
          setShowRegister(!showRegister);
          setError("");
          setNotice("");
        }}
      >
        {showRegister
          ? "Already have an account? Log in"
          : "New here? Create account"}
      </button>
    </main>
  );
}

  return (
    <main className="page">
      <h1>Campus Study Group Finder</h1>
      <p>Welcome, {auth.student.name}!</p>
      <button type="button" onClick={handleLogout}>
      Log out
      </button>

      {!loading && !error && (
        <CreateSession
          token={token}
          onCreated={(newSession) =>
            setSessions((previous) => [...previous, newSession])
          }
        />
      )}

      {loading && <p>Loading study groups...</p>}
      {error && <p role="alert">Error: {error}</p>}

      {!loading && !error && sessions.length === 0 && (
        <p>No study groups yet.</p>
      )}

      <label className="search-field">
        Search study groups
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search course or topic..."
        />
      </label>

      <label>
        <input
          type="checkbox"
          checked={onlyJoined}
          onChange={(event) => setOnlyJoined(event.target.checked)}
        />
        {" "}My groups only
      </label>

      {!loading && !error &&
        sessions.length > 0 && filteredSessions.length === 0 && (
          <p>No matching study groups.</p>
        )}

      <div className="session-list">
        {filteredSessions.map((session) => (
          <article className="session-card" key={session.id}>
            <h2>{session.course}</h2>
            <p><strong>Topic:</strong> {session.topic}</p>
            <p><strong>Location:</strong> {session.location}</p>
            <p>
              <strong>Participants:</strong>{" "}
              {session.participant_count ?? 0}
              {" / "}
              {session.max_participants}
            </p>

            <GroupMembership
              session={session}
              token={token}
              onUpdated={setSessions}
            />
          </article>
        ))}
      </div>
    </main>
  );
}

export default App;