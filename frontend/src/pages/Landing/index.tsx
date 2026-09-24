import { useNavigate } from "react-router-dom";
import { ArrowRight, Mail, Zap, Target, LayoutDashboard } from "lucide-react";
import "./landing.css";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing">
      {/* Nav */}
      <nav className="landing-nav">
        <div className="landing-nav__brand">
          <span className="brand-mark">H</span>HireIQ
        </div>
        <div className="landing-nav__actions">
          <button className="btn btn-ghost btn-sm" onClick={() => navigate("/login")}>Sign in</button>
          <button className="btn btn-primary btn-sm" onClick={() => navigate("/register")}>Get started</button>
        </div>
      </nav>

      {/* Hero */}
      <section className="landing-hero">
        <div className="landing-hero__eyebrow">Technical Screening, Automated</div>
        <h1 className="landing-hero__headline">
          Screen candidates in minutes,<br />
          <span className="headline-accent">not weeks.</span>
        </h1>
        <p className="landing-hero__sub">
          Send a tailored MCQ interview to any candidate in seconds. Get scored results
          the moment they finish — so your team reviews only the ones that matter.
        </p>
        <div className="landing-hero__cta">
          <button className="btn btn-primary btn-lg" onClick={() => navigate("/register")}>
            <span style={{marginRight: 6}}>Start hiring smarter</span> <ArrowRight size={16} />
          </button>
          <button className="btn btn-ghost btn-lg" onClick={() => navigate("/login")}>
            Sign in to dashboard
          </button>
        </div>

        {/* Stats row */}
        <div className="landing-stats">
          <div className="stat-item">
            <span className="stat-number">2 min</span>
            <span className="stat-label">to send an invite</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-number">AI-scored</span>
            <span className="stat-label">no manual grading</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-number">Real-time</span>
            <span className="stat-label">dashboard updates</span>
          </div>
        </div>
      </section>

      {/* Features — asymmetric grid */}
      <section className="landing-features">
        <div className="features-header">
          <h2>Built for technical teams</h2>
          <p>Every detail of the process is designed around how engineering teams actually hire.</p>
        </div>

        <div className="features-grid">
          <div className="feature-card feature-card--large">
            <div className="feature-card__icon"><Mail size={24} color="var(--blue)" /></div>
            <h3>One-click candidate invites</h3>
            <p>Enter the role, tech stack, and difficulty level. HireIQ generates a custom interview and sends a branded email — no templates to maintain.</p>
          </div>
          <div className="feature-card">
            <div className="feature-card__icon"><Zap size={24} color="var(--blue)" /></div>
            <h3>Instant scoring</h3>
            <p>Results appear on your dashboard the moment a candidate submits. Score breakdown per question included.</p>
          </div>
          <div className="feature-card">
            <div className="feature-card__icon"><Target size={24} color="var(--blue)" /></div>
            <h3>Tailored MCQs per role</h3>
            <p>Questions are generated fresh for each candidate based on their specific stack — not recycled from a question bank.</p>
          </div>
          <div className="feature-card feature-card--wide">
            <div className="feature-card__icon"><LayoutDashboard size={24} color="var(--blue)" /></div>
            <h3>Live dashboard</h3>
            <p>See at a glance who has opened their link, who's in progress, and who's completed. Status updates in real time without refreshing.</p>
          </div>
        </div>
      </section>

      {/* CTA strip */}
      <section className="landing-cta-strip">
        <h2>Ready to cut your screening time in half?</h2>
        <button className="btn btn-primary btn-lg" onClick={() => navigate("/register")}>
          <span style={{marginRight: 6}}>Create your account</span> <ArrowRight size={16} />
        </button>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <span>© 2026 HireIQ · Technical Screening Platform</span>
      </footer>
    </div>
  );
}
