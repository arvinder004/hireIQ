import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../lib/api";
import type { CandidateInterview, Answer } from "../../lib/api";
import { AlertTriangle, ArrowRight, ArrowLeft } from "lucide-react";
import "./interview.css";

type Phase = "loading" | "error" | "intro" | "active" | "submitting" | "complete";

export default function InterviewPage() {
  const { token } = useParams<{ token: string }>();
  const [interview, setInterview] = useState<CandidateInterview | null>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [errorMsg, setErrorMsg] = useState("");
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<number, "A" | "B" | "C" | "D">>({});
  const [result, setResult] = useState<{ score: number; correct: number; total: number } | null>(null);

  useEffect(() => {
    if (!token) return;
    api.getInterview(token)
      .then((data) => {
        if (!data.questions || data.questions.length === 0) {
          setErrorMsg("This interview link is invalid or the questions failed to generate.");
          setPhase("error");
          return;
        }
        if (data.status === "completed") {
          setErrorMsg("This interview has already been completed.");
          setPhase("error");
          return;
        }
        setInterview(data);
        setPhase("intro");
      })
      .catch((e) => {
        setErrorMsg(e.message);
        setPhase("error");
      });
  }, [token]);

  const select = (qid: number, key: "A" | "B" | "C" | "D") => {
    setAnswers((prev) => ({ ...prev, [qid]: key }));
  };

  const submit = async () => {
    if (!token || !interview) return;
    const answerList: Answer[] = interview.questions.map((q) => ({
      question_id: q.id,
      selected: answers[q.id] ?? "A",
    }));
    setPhase("submitting");
    try {
      const res = await api.submitAnswers(token, answerList);
      setResult(res);
      setPhase("complete");
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Submission failed.");
      setPhase("error");
    }
  };

  const progress = interview
    ? Math.round((Object.keys(answers).length / interview.questions.length) * 100)
    : 0;

  const q = interview?.questions[currentQ];

  if (phase === "loading") {
    return (
      <div className="interview-shell">
        <div className="interview-loader">
          <span className="spinner spinner--dark" style={{ width: 32, height: 32 }} />
          <p>Loading your interview…</p>
        </div>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="interview-shell">
        <div className="interview-error-card card">
          <div className="interview-error-icon"><AlertTriangle size={36} color="var(--red)" /></div>
          <h2>Unable to load interview</h2>
          <p>{errorMsg}</p>
        </div>
      </div>
    );
  }

  if (phase === "complete" && result) {
    return (
      <div className="interview-intro-shell">
        <div className="complete-card">
          <div className="brand-mark-large" style={{ margin: "0 auto 32px" }}>H</div>
          <h2 style={{ marginBottom: 16 }}>Assessment Complete</h2>
          <p style={{ color: "var(--ink-muted)", fontSize: 16, marginBottom: 32 }}>
            Thank you for completing the technical assessment for <strong>{interview?.company_name}</strong>.
          </p>
          <div className="complete-note">
            Your responses have been successfully submitted. You may now close this window. 
            The hiring team will be in touch with next steps.
          </div>
        </div>
      </div>
    );
  }

  if (phase === "intro" && interview) {
    return (
      <div className="interview-intro-shell">
        <div className="intro-split">
          <div className="intro-left">
            <div className="brand-mark-large">H</div>
            <h1 className="intro-title">
              Technical Assessment for<br/>
              <span className="text-highlight">{interview.position}</span>
            </h1>
            <p className="intro-subtitle">
              Welcome, {interview.candidate_name}. You have been invited by <strong>{interview.company_name}</strong> to complete this technical screening.
            </p>
          </div>
          <div className="intro-right">
            <div className="intro-details-card">
              <h3 className="details-heading">Assessment Details</h3>
              
              <div className="detail-row">
                <span className="detail-label">Format</span>
                <span className="detail-val">{interview.num_questions} Multiple-Choice</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Level</span>
                <span className="detail-val" style={{ textTransform: "capitalize" }}>{interview.difficulty}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Topics</span>
                <span className="detail-val">{interview.tech_stack}</span>
              </div>

              <div className="detail-note">
                Your responses will be recorded and sent directly to the hiring team upon submission. 
                Ensure you have a stable connection before beginning.
              </div>

              <button 
                className="btn btn-primary btn-start" 
                onClick={() => setPhase("active")}
              >
                <span style={{marginRight: 6}}>Begin Assessment</span> <span className="arrow"><ArrowRight size={16} /></span>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }


  if (!interview || !q) return null;

  const isAnswered = (id: number) => id in answers;
  const allAnswered = interview.questions.every((qq) => isAnswered(qq.id));

  return (
    <div className="interview-active-shell">
      {/* Progress */}
      <div className="interview-progress-bar">
        <div className="interview-progress-fill" style={{ width: `${progress}%` }} />
      </div>

      {/* Header */}
      <header className="active-header">
        <div className="header-brand">
          <span className="brand-mark-small">H</span>
          <span className="brand-name">HireIQ</span>
        </div>
        <div className="header-meta">
          <span className="header-role">{interview.position}</span>
          <span className="header-company">@ {interview.company_name}</span>
        </div>
      </header>

      <div className="active-body">
        {/* Navigation Sidebar */}
        <aside className="active-sidebar">
          <div className="nav-header">Questions</div>
          <nav className="nav-list">
            {interview.questions.map((qq, i) => (
              <button
                key={qq.id}
                className={`nav-item ${i === currentQ ? "is-current" : ""} ${isAnswered(qq.id) ? "is-answered" : ""}`}
                onClick={() => setCurrentQ(i)}
              >
                <span className="nav-num">{String(i + 1).padStart(2, '0')}</span>
                <span className="nav-dot" />
              </button>
            ))}
          </nav>
        </aside>

        {/* Question Area */}
        <main className="active-main">
          <div className="question-container">
            <div className="question-meta">
              <span className="q-label">Question {currentQ + 1}</span>
              <span className="q-topic">{q.topic}</span>
            </div>
            
            <h2 className="question-heading">{q.question}</h2>

            <div className="options-grid">
              {q.options.map((opt) => (
                <button
                  key={opt.key}
                  className={`opt-card ${answers[q.id] === opt.key ? "is-selected" : ""}`}
                  onClick={() => select(q.id, opt.key)}
                >
                  <div className="opt-key">{opt.key}</div>
                  <div className="opt-text">{opt.text}</div>
                </button>
              ))}
            </div>

            <div className="question-actions">
              <button
                className="btn btn-ghost"
                onClick={() => setCurrentQ((c) => Math.max(0, c - 1))}
                disabled={currentQ === 0}
              >
                <ArrowLeft size={16} /> <span style={{marginLeft: 6}}>Previous</span>
              </button>

              {currentQ < interview.questions.length - 1 ? (
                <button
                  className="btn btn-secondary"
                  onClick={() => setCurrentQ((c) => c + 1)}
                >
                  <span style={{marginRight: 6}}>Next</span> <ArrowRight size={16} />
                </button>
              ) : (
                <button
                  className="btn btn-primary"
                  onClick={submit}
                  disabled={!allAnswered || phase === "submitting"}
                >
                  {phase === "submitting" ? "Submitting…" : <><span style={{marginRight: 6}}>Submit Assessment</span> <ArrowRight size={16} /></>}
                </button>
              )}
            </div>
            
            {!allAnswered && currentQ === interview.questions.length - 1 && (
              <div className="missing-alert">
                <AlertTriangle size={16} style={{ marginBottom: -3, marginRight: 6 }} /> You have {interview.questions.filter((qq) => !isAnswered(qq.id)).length} unanswered questions.
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
