import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../../lib/api";
import { ArrowRight } from "lucide-react";
import "./auth.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { access_token, user } = await api.login(form.email, form.password);
      localStorage.setItem("hireiq_token", access_token);
      localStorage.setItem("hireiq_user", JSON.stringify(user));
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-layout">
      <div className="auth-panel">
        <Link to="/" className="auth-brand">
          <span className="brand-mark">H</span>HireIQ
        </Link>
        <div className="auth-header">
          <h1>Welcome back</h1>
          <p>Sign in to your HR dashboard</p>
        </div>

        <form className="auth-form" onSubmit={submit}>
          <div className="field-group">
            <label className="field-label">Work email</label>
            <input
              id="login-email"
              type="email"
              className="field-input"
              placeholder="you@company.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>

          <div className="field-group">
            <label className="field-label">Password</label>
            <input
              id="login-password"
              type="password"
              className="field-input"
              placeholder="••••••••"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>

          {error && <p className="auth-error">{error}</p>}

          <button id="login-submit" type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%", justifyContent: "center" }}>
            {loading ? <span className="spinner" /> : <><span style={{marginRight: 6}}>Sign in</span> <ArrowRight size={16} /></>}
          </button>
        </form>

        <p className="auth-footer-text">
          Don't have an account?{" "}
          <Link to="/register" className="auth-link">Create one</Link>
        </p>
      </div>

      <div className="auth-visual">
        <div className="auth-visual__content">
          <blockquote>"We reduced screening time from 5 days to 3 hours."</blockquote>
          <cite>— Engineering Lead, Series B startup</cite>
        </div>
      </div>
    </div>
  );
}
