const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────
export interface HRUser {
  id: string;
  company_id: string;
  company_name: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface Invite {
  id: string;
  token: string;
  candidate_name: string;
  candidate_email: string;
  position: string;
  tech_stack: string;
  difficulty: string;
  num_questions: number;
  status: "generating" | "invited" | "opened" | "in_progress" | "completed" | "expired" | "failed" | "archived";
  score: number | null;
  sent_at: string;
  opened_at: string | null;
  completed_at: string | null;
}

export interface MCQOption { key: "A" | "B" | "C" | "D"; text: string; }
export interface MCQQuestion {
  id: number;
  question: string;
  topic: string;
  options: MCQOption[];
}
export interface CandidateInterview {
  id: string;
  candidate_name: string;
  position: string;
  company_name: string;
  difficulty: string;
  tech_stack: string;
  num_questions: number;
  status: string;
  questions: MCQQuestion[];
}
export interface Answer { question_id: number; selected: "A" | "B" | "C" | "D"; }
export interface SubmitResult { score: number; correct: number; total: number; status: string; }
export interface CreateInvitePayload {
  candidate_name: string;
  candidate_email: string;
  position: string;
  tech_stack: string;
  difficulty: string;
  num_questions: number;
}

// ── HTTP helper ───────────────────────────────────────────────────
async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("hireiq_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── API client ────────────────────────────────────────────────────
export const api = {
  // Auth
  register: (data: { company_name: string; name: string; email: string; password: string }) =>
    req<{ access_token: string; user: HRUser }>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  login: (email: string, password: string) =>
    req<{ access_token: string; user: HRUser }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => req<HRUser>("/api/v1/auth/me"),

  // Invites
  createInvite: (data: CreateInvitePayload) =>
    req<{ id: string; token: string; status: string }>("/api/v1/invites", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listInvites: () => req<Invite[]>("/api/v1/invites"),
  getInvite: (id: string) => req<Invite>(`/api/v1/invites/${id}`),
  deleteInvite: (id: string) => req<void>(`/api/v1/invites/${id}`, { method: "DELETE" }),
  archiveInvite: (id: string) => req<{ message: string }>(`/api/v1/invites/${id}/archive`, { method: "POST" }),

  // Candidate
  getInterview: (token: string) => req<CandidateInterview>(`/api/v1/candidate/${token}`),
  submitAnswers: (token: string, answers: Answer[]) =>
    req<SubmitResult>(`/api/v1/candidate/${token}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),
  sendEmail: (id: string, subject: string, body: string, type: string) => 
    req<{ message: string }>(`/api/v1/invites/${id}/email`, {
      method: "POST",
      body: JSON.stringify({ subject, body, type }),
    }),
};
