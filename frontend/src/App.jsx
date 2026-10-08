import { useEffect, useState } from "react";
import "./App.css";
import CreateSession from "./CreateSession";
import GroupMembership from "./GroupMembership";

function App() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [onlyJoined, setOnlyJoined] = useState(false);

  useEffect(() => {
    let ignore = false;

    async function loadSessions() {
      try {
        const response = await fetch(
         "http://127.0.0.1:8000/sessions?student_id=1"
     );

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
  }, []);

   const query = search.trim().toLowerCase();

const filteredSessions = sessions.filter((session) => {
  const matchesSearch =
    session.course.toLowerCase().includes(query) ||
    session.topic.toLowerCase().includes(query);

  const matchesMembership = !onlyJoined || session.joined;

  return matchesSearch && matchesMembership;
  });

  return (
    <main className="page">
      <h1>Campus Study Group Finder</h1>
      <p>Find classmates and study together.</p>
      {!loading && !error && (
  <CreateSession
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
              {session.participant_count ?? 0} / {session.max_participants}

            </p>
            <GroupMembership
              session={session}
               onUpdated={setSessions}
              />
          </article>
        ))}
      </div>
    </main>
  );
}

export default App;