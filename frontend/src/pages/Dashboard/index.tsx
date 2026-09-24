import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../../lib/api";
import type { Invite, HRUser } from "../../lib/api";
import { ClipboardList, Archive, Inbox, X } from "lucide-react";
import ScheduleModal from "./ScheduleModal";
import MailEditorModal from "./MailEditorModal";
import "./dashboard.css";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function StatusBadge({ status }: { status: string }) {
  const labels: Record<string, string> = {
    generating: "Generating", invited: "Invited", opened: "Opened",
    in_progress: "In Progress", completed: "Completed", expired: "Expired",
    failed: "Failed", archived: "Archived",
  };
  return (
    <span className={`badge badge--${status}`}>
      <span className="badge-dot" />
      {labels[status] ?? status}
    </span>
  );
}

function ScoreBar({ score }: { score: number | null }) {
  if (score === null) return <span style={{ color: "var(--ink-muted)", fontSize: 13 }}>—</span>;
  const color = score >= 70 ? "var(--green)" : score >= 40 ? "var(--amber)" : "var(--red)";
  return (
    <div className="score-bar-wrap">
      <div className="score-bar">
        <div className="score-bar__fill" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="score-label" style={{ color }}>{score}%</span>
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [invites, setInvites] = useState<Invite[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSchedule, setShowSchedule] = useState(false);
  const [retryData, setRetryData] = useState<Partial<Invite> | undefined>(undefined);
  const [selectedInvite, setSelectedInvite] = useState<Invite | null>(null);
  const [mailType, setMailType] = useState<"rejection" | "next_steps" | null>(null);
  const [activeTab, setActiveTab] = useState<"active" | "archived">("active");
  const user: HRUser | null = JSON.parse(localStorage.getItem("hireiq_user") ?? "null");
  const evtRef = useRef<EventSource | null>(null);

  const load = async () => {
    try {
      const data = await api.listInvites();
      setInvites(data);
    } catch {
      navigate("/login");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();

    // SSE for real-time status updates
    if (user?.company_id) {
      const es = new EventSource(`${BASE}/api/v1/candidate/stream/${user.company_id}`);
      evtRef.current = es;
      es.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === "status_update") {
            setInvites((prev) =>
              prev.map((inv) =>
                inv.id === msg.invite_id
                  ? { ...inv, status: msg.status, score: msg.score ?? inv.score }
                  : inv
              )
            );
          }
        } catch { /* ignore */ }
      };
      es.onerror = () => es.close();
    }

    return () => evtRef.current?.close();
  }, []);

  const logout = () => {
    localStorage.removeItem("hireiq_token");
    localStorage.removeItem("hireiq_user");
    navigate("/login");
  };

  const handleArchive = async (id: string) => {
    try {
      await api.archiveInvite(id);
      setSelectedInvite(null);
      load();
      toast.success("Candidate archived successfully");
    } catch (e) {
      toast.error("Failed to archive candidate.");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this candidate? This action cannot be undone.")) return;
    try {
      await api.deleteInvite(id);
      setSelectedInvite(null);
      load();
      toast.success("Candidate deleted");
    } catch (e) {
      toast.error("Failed to delete candidate.");
    }
  };

  // Stats
  const activeInvites = invites.filter((i) => i.status !== "archived");
  const archivedInvites = invites.filter((i) => i.status === "archived");
  
  const displayedInvites = activeTab === "active" ? activeInvites : archivedInvites;

  const stats = {
    total: invites.length,
    completed: invites.filter((i) => i.status === "completed").length,
    pending: invites.filter((i) => ["invited", "opened", "in_progress"].includes(i.status)).length,
    avgScore: (() => {
      const scored = invites.filter((i) => i.score !== null);
      if (!scored.length) return null;
      return Math.round(scored.reduce((s, i) => s + (i.score ?? 0), 0) / scored.length);
    })(),
  };

  return (
    <div className="dashboard">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar__brand">
          <span className="brand-mark">H</span>
          <span>HireIQ</span>
        </div>
        <nav className="sidebar__nav">
          <a href="#" className="sidebar__link sidebar__link--active">
            <ClipboardList size={18} /> Interviews
          </a>
        </nav>
        <div className="sidebar__bottom">
          <div className="sidebar__user">
            <div className="user-avatar">{user?.name?.[0] ?? "H"}</div>
            <div>
              <div className="user-name">{user?.name}</div>
              <div className="user-company">{user?.company_name}</div>
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={logout}>Sign out</button>
        </div>
      </aside>

      {/* Main */}
      <main className="dashboard-main">
        <header className="dash-header">
          <div>
            <h1 className="dash-title">Interviews</h1>
            <p className="dash-sub">
              {user?.company_name} · {invites.length} total
            </p>
          </div>
          <button id="schedule-btn" className="btn btn-primary" onClick={() => {
            setRetryData(undefined);
            setShowSchedule(true);
          }}>
            + Schedule Interview
          </button>
        </header>

        {/* Stats */}
        <div className="stats-row">
          <div className="stat-card">
            <span className="stat-card__value">{stats.total}</span>
            <span className="stat-card__label">Total Sent</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__value">{stats.completed}</span>
            <span className="stat-card__label">Completed</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__value">{stats.pending}</span>
            <span className="stat-card__label">In Progress</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__value">
              {stats.avgScore !== null ? `${stats.avgScore}%` : "—"}
            </span>
            <span className="stat-card__label">Avg. Score</span>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 16, marginBottom: 16, borderBottom: "1px solid var(--border)", paddingBottom: 0 }}>
          <button 
            style={{ padding: "8px 16px", background: "none", border: "none", borderBottom: activeTab === "active" ? "2px solid var(--primary)" : "2px solid transparent", color: activeTab === "active" ? "var(--ink)" : "var(--ink-muted)", fontWeight: activeTab === "active" ? 600 : 400, cursor: "pointer", fontSize: 14 }}
            onClick={() => setActiveTab("active")}
          >
            Active Candidates ({activeInvites.length})
          </button>
          <button 
            style={{ padding: "8px 16px", background: "none", border: "none", borderBottom: activeTab === "archived" ? "2px solid var(--primary)" : "2px solid transparent", color: activeTab === "archived" ? "var(--ink)" : "var(--ink-muted)", fontWeight: activeTab === "archived" ? 600 : 400, cursor: "pointer", fontSize: 14 }}
            onClick={() => setActiveTab("archived")}
          >
            Archived ({archivedInvites.length})
          </button>
        </div>

        {/* Table */}
        <div className="card table-card">
          {loading ? (
            <div className="table-empty"><span className="spinner spinner--dark" /></div>
          ) : displayedInvites.length === 0 ? (
            <div className="table-empty">
              <div style={{ color: "var(--ink-muted)", marginBottom: 12 }}>
                {activeTab === "archived" ? <Archive size={32} /> : <Inbox size={32} />}
              </div>
              <p>{activeTab === "archived" ? "No archived candidates." : "No active interviews."}</p>
              {activeTab === "active" && (
                <button className="btn btn-primary btn-sm" onClick={() => {
                  setRetryData(undefined);
                  setShowSchedule(true);
                }}>
                  Schedule your first interview
                </button>
              )}
            </div>
          ) : (
            <table className="inv-table">

              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Position</th>
                  <th>Difficulty</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Sent</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {displayedInvites.map((inv) => (
                  <tr key={inv.id} className="inv-row" onClick={() => setSelectedInvite(inv)}>
                    <td>
                      <div className="candidate-cell">
                        <div className="candidate-avatar">{inv.candidate_name[0]}</div>
                        <div>
                          <div className="candidate-name">{inv.candidate_name}</div>
                          <div className="candidate-email">{inv.candidate_email}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="position-cell">{inv.position}</div>
                      <div className="tech-stack-cell">{inv.tech_stack}</div>
                    </td>
                    <td><span className={`diff-pill diff-pill--${inv.difficulty}`}>{inv.difficulty}</span></td>
                    <td><StatusBadge status={inv.status} /></td>
                    <td><ScoreBar score={inv.score} /></td>
                    <td className="date-cell">{new Date(inv.sent_at).toLocaleDateString()}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      {inv.status === "failed" ? (
                        <button
                          className="btn btn-ghost btn-sm"
                          style={{ color: "var(--red)" }}
                          onClick={() => {
                            setRetryData(inv);
                            setShowSchedule(true);
                          }}
                        >
                          Retry
                        </button>
                      ) : (
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={() => {
                            navigator.clipboard.writeText(`${window.location.origin}/interview/${inv.token}`);
                            toast.success("Interview link copied!");
                          }}
                        >
                          Copy link
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Invite Detail Drawer */}
        {selectedInvite && (
          <div className="drawer-overlay" onClick={() => setSelectedInvite(null)}>
            <aside className="drawer" onClick={(e) => e.stopPropagation()}>
              <div className="drawer-header">
                <h2>{selectedInvite.candidate_name}</h2>
                <button className="drawer-close" onClick={() => setSelectedInvite(null)}>
                  <X size={20} />
                </button>
              </div>
              <div className="drawer-section">
                <div className="drawer-row"><span>Email</span><span>{selectedInvite.candidate_email}</span></div>
                <div className="drawer-row"><span>Position</span><span>{selectedInvite.position}</span></div>
                <div className="drawer-row"><span>Tech Stack</span><span>{selectedInvite.tech_stack}</span></div>
                <div className="drawer-row"><span>Difficulty</span><span style={{ textTransform: "capitalize" }}>{selectedInvite.difficulty}</span></div>
                <div className="drawer-row"><span>Questions</span><span>{selectedInvite.num_questions}</span></div>
                <div className="drawer-row"><span>Status</span><StatusBadge status={selectedInvite.status} /></div>
                {selectedInvite.score !== null && (
                  <div className="drawer-row"><span>Score</span><ScoreBar score={selectedInvite.score} /></div>
                )}
                {selectedInvite.opened_at && (
                  <div className="drawer-row"><span>Opened</span><span>{new Date(selectedInvite.opened_at).toLocaleString()}</span></div>
                )}
                {selectedInvite.completed_at && (
                  <div className="drawer-row"><span>Completed</span><span>{new Date(selectedInvite.completed_at).toLocaleString()}</span></div>
                )}
              </div>
              <div style={{ padding: "0 24px 24px", display: "flex", flexDirection: "column", gap: 8 }}>
                <button
                  className="btn btn-ghost"
                  style={{ width: "100%", justifyContent: "center" }}
                  onClick={() => {
                    navigator.clipboard.writeText(`${window.location.origin}/interview/${selectedInvite.token}`);
                    toast.success("Interview link copied!");
                  }}
                >
                  Copy interview link
                </button>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-ghost" style={{ flex: 1, justifyContent: "center", color: "var(--amber)", borderColor: "var(--amber)" }} onClick={() => setMailType("next_steps")}>
                    Next Steps
                  </button>
                  {selectedInvite.status !== "archived" && (
                    <button className="btn btn-ghost" style={{ flex: 1, justifyContent: "center", color: "var(--red)", borderColor: "var(--red)" }} onClick={() => setMailType("rejection")}>
                      Rejection
                    </button>
                  )}
                </div>
                {selectedInvite.status !== "archived" ? (
                  <button
                    className="btn btn-ghost"
                    style={{ width: "100%", justifyContent: "center", color: "var(--ink-muted)", marginTop: 16 }}
                    onClick={() => handleArchive(selectedInvite.id)}
                  >
                    Archive Candidate
                  </button>
                ) : (
                  <button
                    className="btn btn-ghost"
                    style={{ width: "100%", justifyContent: "center", color: "var(--red)", marginTop: 16 }}
                    onClick={() => handleDelete(selectedInvite.id)}
                  >
                    Delete Candidate (Permanent)
                  </button>
                )}
              </div>
            </aside>
          </div>
        )}
      </main>

      {/* Schedule Modal */}

      {showSchedule && (
        <ScheduleModal
          initialData={retryData as any}
          onClose={() => setShowSchedule(false)}
          onCreated={() => { setShowSchedule(false); load(); }}
        />
      )}

      {/* Mail Editor Modal */}
      {mailType && selectedInvite && (
        <MailEditorModal
          invite={selectedInvite}
          type={mailType}
          companyName={user?.company_name ?? ""}
          onClose={() => setMailType(null)}
          onSuccess={() => {
            load();
            setSelectedInvite(null);
          }}
        />
      )}
    </div>
  );
}
