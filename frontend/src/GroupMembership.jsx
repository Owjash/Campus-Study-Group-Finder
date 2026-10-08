import { useState } from "react";

function GroupMembership({ session, onUpdated }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const full =
    (session.participant_count ?? 0) >= session.max_participants;

  async function handleClick() {
    setBusy(true);
    setError("");

    const action = session.joined ? "leave" : "join";

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/sessions/${session.id}/${action}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ student_id: 1 }),
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Could not update membership.");
      }

      const updatedResponse = await fetch(
        "http://127.0.0.1:8000/sessions?student_id=1"
      );

      if (!updatedResponse.ok) {
        throw new Error("Membership saved. Refresh to see the update.");
      }

      const updatedSessions = await updatedResponse.json();
      onUpdated(updatedSessions);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleClick}
        disabled={busy || (!session.joined && full)}
      >
        {busy
          ? "Updating..."
          : session.joined
            ? "Leave group"
            : full
              ? "Group full"
              : "Join group"}
      </button>

      {error && <p role="alert">{error}</p>}
    </div>
  );
}

export default GroupMembership;