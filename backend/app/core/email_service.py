"""
Email service using standard SMTP (Gmail).
Set SMTP_EMAIL and SMTP_PASSWORD in your .env to enable.
"""
import smtplib
from email.message import EmailMessage
import asyncio

from app.config import settings
from app.core.logging import log


def _html_body(
    candidate_name: str,
    position: str,
    company_name: str,
    interview_url: str,
    num_questions: int,
    difficulty: str,
) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1"/></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:Inter,-apple-system,sans-serif;">
  <div style="max-width:560px;margin:40px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

    <div style="background:#0F172A;padding:32px 40px;">
      <div style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">
        HireIQ <span style="color:#F59E0B;">·</span> Interview Invitation
      </div>
    </div>

    <div style="padding:40px;">
      <p style="font-size:16px;color:#334155;margin:0 0 20px;">Hi <strong>{candidate_name}</strong>,</p>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 24px;">
        <strong>{company_name}</strong> has invited you to complete a technical screening
        for the <strong>{position}</strong> role.
      </p>

      <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:20px 24px;margin:0 0 28px;">
        <div style="font-size:12px;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;font-weight:700;margin-bottom:12px;">Interview Details</div>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:5px 0;color:#64748B;font-size:14px;width:40%">Position</td>
              <td style="padding:5px 0;color:#0F172A;font-size:14px;font-weight:600">{position}</td></tr>
          <tr><td style="padding:5px 0;color:#64748B;font-size:14px">Format</td>
              <td style="padding:5px 0;color:#0F172A;font-size:14px;font-weight:600">{num_questions} multiple-choice questions</td></tr>
          <tr><td style="padding:5px 0;color:#64748B;font-size:14px">Level</td>
              <td style="padding:5px 0;color:#0F172A;font-size:14px;font-weight:600;text-transform:capitalize">{difficulty}</td></tr>
          <tr><td style="padding:5px 0;color:#64748B;font-size:14px">Expires</td>
              <td style="padding:5px 0;color:#0F172A;font-size:14px;font-weight:600">7 days from today</td></tr>
        </table>
      </div>

      <a href="{interview_url}"
         style="display:inline-block;background:#2563EB;color:#ffffff;text-decoration:none;
                padding:14px 32px;border-radius:8px;font-size:15px;font-weight:600;">
        Start Interview →
      </a>

      <p style="font-size:13px;color:#94A3B8;margin:28px 0 0;line-height:1.6;">
        If you weren't expecting this, you can safely ignore it.<br/>
        This link works only once and expires in 7 days.
      </p>
    </div>

    <div style="background:#F8FAFC;padding:20px 40px;border-top:1px solid #E2E8F0;">
      <p style="font-size:12px;color:#94A3B8;margin:0;">
        Sent via <strong>HireIQ</strong> — Automated Technical Screening
      </p>
    </div>
  </div>
</body>
</html>"""


def _send_smtp(to_email: str, subject: str, html_body: str) -> bool:
    if not settings.smtp_email or not settings.smtp_password:
        log.warning("SMTP_EMAIL or SMTP_PASSWORD not set — skipping email send.")
        return False
        
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_email}>"
    msg['To'] = to_email
    
    # We set content as HTML
    msg.set_content(html_body, subtype='html')
    
    try:
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_email, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        log.error(f"SMTP email failed for {to_email}: {e}")
        return False


async def send_interview_invite(
    candidate_name: str,
    candidate_email: str,
    position: str,
    company_name: str,
    interview_url: str,
    num_questions: int,
    difficulty: str,
) -> bool:
    """Send interview invitation via SMTP."""
    html_content = _html_body(
        candidate_name=candidate_name,
        position=position,
        company_name=company_name,
        interview_url=interview_url,
        num_questions=num_questions,
        difficulty=difficulty,
    )
    subject = f"Interview Invitation: {position} at {company_name}"
    
    # Run sync smtplib in a thread
    success = await asyncio.to_thread(_send_smtp, candidate_email, subject, html_content)
    if success:
        log.info(f"Invite email sent via SMTP → {candidate_email} ({position})")
    return success


async def send_custom_email(
    to_email: str,
    subject: str,
    body: str,
) -> bool:
    """Send a custom email via SMTP."""
    # Convert simple newlines to <br> for HTML rendering
    html_body = body.replace("\n", "<br>")
    full_html = f'<div style="font-family:sans-serif;font-size:15px;color:#334155;line-height:1.6;">{html_body}</div>'
    
    success = await asyncio.to_thread(_send_smtp, to_email, subject, full_html)
    if success:
        log.info(f"Custom email sent via SMTP → {to_email}")
    return success
