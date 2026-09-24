import { useState } from "react";
import { api } from "../../lib/api";
import type { CreateInvitePayload } from "../../lib/api";
import { X, ArrowRight } from "lucide-react";

interface Props {
  onClose: () => void;
  onCreated: () => void;
  initialData?: Partial<CreateInvitePayload>;
}

export default function ScheduleModal({ onClose, onCreated, initialData }: Props) {
  const [form, setForm] = useState({
    candidate_name: initialData?.candidate_name ?? "",
    candidate_email: initialData?.candidate_email ?? "",
    position: initialData?.position ?? "",
    tech_stack: initialData?.tech_stack ?? "",
    difficulty: initialData?.difficulty ?? "mid",
    num_questions: initialData?.num_questions ?? 5,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.createInvite({ ...form, num_questions: Number(form.num_questions) });
      onCreated();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create invite.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Schedule Interview</h2>
          <button className="drawer-close" onClick={onClose}><X size={20} /></button>
        </div>

        <form className="modal-form" onSubmit={submit}>
          <div className="modal-grid">
            <div className="field-group">
              <label className="field-label">Candidate name</label>
              <input id="inv-name" className="field-input" placeholder="Jane Doe" required
                value={form.candidate_name}
                onChange={(e) => setForm({ ...form, candidate_name: e.target.value })} />
            </div>
            <div className="field-group">
              <label className="field-label">Candidate email</label>
              <input id="inv-email" type="email" className="field-input" placeholder="jane@example.com" required
                value={form.candidate_email}
                onChange={(e) => setForm({ ...form, candidate_email: e.target.value })} />
            </div>
          </div>

          <div className="field-group">
            <label className="field-label">Position / Role</label>
            <input id="inv-position" className="field-input" placeholder="e.g. Backend Engineer" required
              value={form.position}
              onChange={(e) => setForm({ ...form, position: e.target.value })} />
          </div>

          <div className="field-group">
            <label className="field-label">Tech stack</label>
            <input id="inv-stack" className="field-input" placeholder="e.g. Python, FastAPI, PostgreSQL" required
              value={form.tech_stack}
              onChange={(e) => setForm({ ...form, tech_stack: e.target.value })} />
            <span className="field-hint">Separate technologies with commas. Questions will be tailored to these.</span>
          </div>

          <div className="modal-grid">
            <div className="field-group">
              <label className="field-label">Difficulty</label>
              <select id="inv-difficulty" className="field-input field-select"
                value={form.difficulty}
                onChange={(e) => setForm({ ...form, difficulty: e.target.value })}>
                <option value="junior">Junior</option>
                <option value="mid">Mid-level</option>
                <option value="senior">Senior</option>
              </select>
            </div>
            <div className="field-group">
              <label className="field-label">Number of questions</label>
              <select id="inv-numq" className="field-input field-select"
                value={form.num_questions}
                onChange={(e) => setForm({ ...form, num_questions: Number(e.target.value) })}>
                {[3, 4, 5, 6, 7, 8, 10].map((n) => (
                  <option key={n} value={n}>{n} questions</option>
                ))}
              </select>
            </div>
          </div>

          {error && <p className="auth-error">{error}</p>}

          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button id="inv-submit" type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner" /> Generating…</> : <><span style={{marginRight: 6}}>Send Interview</span> <ArrowRight size={16} /></>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
