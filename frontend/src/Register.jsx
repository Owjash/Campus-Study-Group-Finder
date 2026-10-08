import { useState } from "react";

function Register({ onRegistered }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/auth/register",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name.trim(),
            email: email.trim(),
            password,
          }),
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : "Check your details and try again."
        );
      }

      onRegistered();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="create-form">
      <h2>Create account</h2>

      <label>
        Name
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          autoComplete="name"
          maxLength={100}
          required
        />
      </label>

      <label>
        Email
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
          required
        />
      </label>

      <label>
        Password (at least 12 characters)
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="new-password"
          minLength={12}
          maxLength={128}
          required
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? "Creating account..." : "Create account"}
      </button>

      {error && <p role="alert">{error}</p>}
    </form>
  );
}

export default Register;
