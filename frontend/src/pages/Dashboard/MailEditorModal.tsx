import { useState, useEffect } from "react";
import { api } from "../../lib/api";
import type { Invite } from "../../lib/api";
import { X, ArrowRight } from "lucide-react";
import { toast } from "sonner";

interface Props {
  invite: Invite;
  type: "rejection" | "next_steps";
  companyName: string;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function MailEditorModal({ invite, type, companyName, onClose, onSuccess }: Props) {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (type === "rejection") {
      setSubject(`Update regarding your application for ${invite.position}`);
      setBody(`Hi ${invite.candidate_name.split(" ")[0]},\n\nThank you for taking the time to complete the technical assessment for the ${invite.position} role at ${companyName}.\n\nWhile we were impressed with your background, we have decided to move forward with other candidates whose experience better aligns with our current needs.\n\nWe appreciate your interest and wish you the best of luck in your job search.\n\nBest regards,\nThe Hiring Team at ${companyName}`);
    } else {
      setSubject(`Next steps for the ${invite.position} role at ${companyName}!`);
      setBody(`Hi ${invite.candidate_name.split(" ")[0]},\n\nThank you for completing the technical assessment for the ${invite.position} role. You did great!\n\nWe would love to invite you to the next round of interviews for ${companyName}. Please let us know your availability for a 30-minute chat later this week.\n\nLooking forward to speaking with you soon.\n\nBest regards,\nThe Hiring Team at ${companyName}`);
    }
  }, [type, invite, companyName]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.sendEmail(invite.id, subject, body, type);
      toast.success("Email sent successfully!");
      if (onSuccess) onSuccess();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to send email.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 600 }}>
        <div className="modal-header">
          <h2>Send {type === "rejection" ? "Rejection" : "Next Steps"} Email</h2>
          <button className="drawer-close" onClick={onClose}><X size={20} /></button>
        </div>

        <form className="modal-form" onSubmit={submit}>
          <div className="field-group">
            <label className="field-label">Subject</label>
            <input className="field-input" required
              value={subject}
              onChange={(e) => setSubject(e.target.value)} />
          </div>

          <div className="field-group">
            <label className="field-label">Message Body</label>
            <textarea className="field-input" required
              style={{ minHeight: 200, resize: "vertical", fontFamily: "inherit", lineHeight: 1.5 }}
              value={body}
              onChange={(e) => setBody(e.target.value)} />
            <span className="field-hint">You can edit the text before sending. Newlines will be preserved.</span>
          </div>

          {error && <p className="auth-error">{error}</p>}

          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner" /> Sending…</> : <><span style={{marginRight: 6}}>Send Email</span> <ArrowRight size={16} /></>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
