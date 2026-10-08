import { useState } from "react";

function CreateSession({ onCreated }) {
  const [course, setCourse] = useState("");
  const [topic, setTopic] = useState("");
  const [location, setLocation] = useState("");
  const [limit, setLimit] = useState(6);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/sessions",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            course: course.trim(),
            topic: topic.trim(),
            location: location.trim(),
            max_participants: Number(limit),
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Could not create group (status ${response.status}).`
        );
      }

      const newSession = await response.json();
      onCreated(newSession);

      setCourse("");
      setTopic("");
      setLocation("");
      setLimit(6);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="create-form" onSubmit={handleSubmit}>
      <h2>Create a study group</h2>

      <label>
        Course
        <input
          value={course}
          onChange={(event) => setCourse(event.target.value)}
          placeholder="CE 3345"
          required
          maxLength={30}
        />
      </label>

      <label>
        Topic
        <input
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          placeholder="Binary trees"
          required
          maxLength={150}
        />
      </label>

      <label>
        Location
        <input
          value={location}
          onChange={(event) => setLocation(event.target.value)}
          placeholder="UTD Library"
          required
          maxLength={150}
        />
      </label>

      <label>
        Participant limit
        <input
          type="number"
          value={limit}
          onChange={(event) => setLimit(event.target.value)}
          min={1}
          max={50}
          required
        />
      </label>

      {error && <p role="alert">{error}</p>}

      <button type="submit" disabled={saving}>
        {saving ? "Creating..." : "Create group"}
      </button>
    </form>
  );
}

export default CreateSession;