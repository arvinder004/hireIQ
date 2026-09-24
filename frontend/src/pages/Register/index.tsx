import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../../lib/api";
import { ArrowRight } from "lucide-react";
import "./auth.css";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ company_name: "", name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) { setError("Password must be at least 8 characters."); return; }
    setError("");
    setLoading(true);
    try {
      const { access_token, user } = await api.register(form);
      localStorage.setItem("hireiq_token", access_token);
      localStorage.setItem("hireiq_user", JSON.stringify(user));
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed.");
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
          <h1>Create your account</h1>
          <p>Set up your company's hiring workspace</p>
        </div>

        <form className="auth-form" onSubmit={submit}>
          <div className="field-group">
            <label className="field-label">Company name</label>
            <input
              id="reg-company"
              type="text"
              className="field-input"
              placeholder="Acme Corp"
              value={form.company_name}
              onChange={(e) => setForm({ ...form, company_name: e.target.value })}
              required
            />
          </div>

          <div className="field-group">
            <label className="field-label">Your name</label>
            <input
              id="reg-name"
              type="text"
              className="field-input"
              placeholder="Jane Smith"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>

          <div className="field-group">
            <label className="field-label">Work email</label>
            <input
              id="reg-email"
              type="email"
              className="field-input"
              placeholder="jane@acme.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>

          <div className="field-group">
            <label className="field-label">Password</label>
            <input
              id="reg-password"
              type="password"
              className="field-input"
              placeholder="Min. 8 characters"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>

          {error && <p className="auth-error">{error}</p>}

          <button id="reg-submit" type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%", justifyContent: "center" }}>
            {loading ? <span className="spinner" /> : <><span style={{marginRight: 6}}>Create account</span> <ArrowRight size={16} /></>}
          </button>
        </form>

        <p className="auth-footer-text">
          Already have an account?{" "}
          <Link to="/login" className="auth-link">Sign in</Link>
        </p>
      </div>

      <div className="auth-visual">
        <div className="auth-visual__content">
          <blockquote>"The quality of candidates we interview has gone up significantly since using automated screening."</blockquote>
          <cite>— Head of Talent, fintech scale-up</cite>
        </div>
      </div>
    </div>
  );
}
