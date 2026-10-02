"""
J.A.R.V.I.S. Gmail Integration Engine
Provides secure IMAP (SSL) & SMTP (TLS) communications with Gmail.
Supports sending emails, reading recent messages, searching, and inbox summarization.
"""
import os
import smtplib
import imaplib
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Dict, Any, Optional, List

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier

logger = logging.getLogger("jarvis.integrations.email")


class GmailTool(BaseTool):
    @property
    def id(self) -> str:
        return "gmail"

    @property
    def name(self) -> str:
        return "Gmail Communications"

    @property
    def description(self) -> str:
        return "Interact with Gmail inbox: send emails, read latest emails, search messages by query, or generate inbox status."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["send", "read", "search", "status"],
                    "description": "Email action: 'send', 'read', 'search', or 'status'."
                },
                "to": {
                    "type": "string",
                    "description": "Recipient email address (for action='send')."
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line (for action='send')."
                },
                "body": {
                    "type": "string",
                    "description": "Email body content (for action='send')."
                },
                "count": {
                    "type": "integer",
                    "description": "Number of recent emails to retrieve (default: 5)."
                },
                "query": {
                    "type": "string",
                    "description": "Search query for action='search' (e.g. sender or subject keyword)."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.APP_CONTROL

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.SENSITIVE

    def _get_credentials(self) -> tuple[Optional[str], Optional[str]]:
        addr = os.environ.get("GMAIL_ADDRESS")
        pwd = os.environ.get("GMAIL_APP_PASSWORD")
        return addr, pwd

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "").lower().strip()
        addr, pwd = self._get_credentials()

        if not addr or not pwd:
            return ToolResult(
                success=False,
                error="Gmail credentials not configured. Please set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in environment."
            )

        try:
            if action == "send":
                to_addr = params.get("to", "").strip()
                subject = params.get("subject", "J.A.R.V.I.S. Automated Notice").strip()
                body = params.get("body", "").strip()

                if not to_addr or not body:
                    return ToolResult(success=False, error="'to' recipient and 'body' are required to send an email.")

                msg = MIMEMultipart()
                msg["From"] = addr
                msg["To"] = to_addr
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as srv:
                    srv.ehlo()
                    srv.starttls()
                    srv.login(addr, pwd)
                    srv.sendmail(addr, to_addr, msg.as_string())

                return ToolResult(success=True, data=f"Email successfully delivered to {to_addr}. Subject: '{subject}'")

            elif action == "read":
                count = min(15, max(1, int(params.get("count", 5))))
                with imaplib.IMAP4_SSL("imap.gmail.com", timeout=12) as mail:
                    mail.login(addr, pwd)
                    mail.select("inbox")
                    _, data = mail.search(None, "ALL")
                    ids = data[0].split()[-count:]
                    messages = []
                    for mid in reversed(ids):
                        _, md = mail.fetch(mid, "(RFC822)")
                        msg = email_lib.message_from_bytes(md[0][1])
                        subj = msg.get("Subject", "(no subject)")
                        frm = msg.get("From", "Unknown")
                        date = msg.get("Date", "")
                        body_preview = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body_preview = payload.decode("utf-8", "ignore")[:150]
                                    break
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                body_preview = payload.decode("utf-8", "ignore")[:150]

                        clean_preview = " ".join(body_preview.split())
                        messages.append(f"📧 From: {frm}\n   Subject: {subj}\n   Date: {date}\n   Preview: {clean_preview}")

                    return ToolResult(
                        success=True,
                        data="\n\n".join(messages) if messages else "No emails found in inbox."
                    )

            elif action == "search":
                q = params.get("query", "").strip()
                if not q:
                    return ToolResult(success=False, error="Search query is required.")

                with imaplib.IMAP4_SSL("imap.gmail.com", timeout=12) as mail:
                    mail.login(addr, pwd)
                    mail.select("inbox")
                    _, data = mail.search(None, f'SUBJECT "{q}"')
                    ids = data[0].split()[-5:]
                    results = []
                    for mid in ids:
                        _, md = mail.fetch(mid, "(RFC822)")
                        msg = email_lib.message_from_bytes(md[0][1])
                        results.append(f"• {msg.get('Subject', '(no subject)')} — from {msg.get('From', '?')}")

                    return ToolResult(
                        success=True,
                        data="\n".join(results) if results else f"No emails found matching subject query '{q}'."
                    )

            elif action == "status":
                with imaplib.IMAP4_SSL("imap.gmail.com", timeout=10) as mail:
                    mail.login(addr, pwd)
                    mail.select("inbox")
                    _, unread = mail.search(None, "UNSEEN")
                    unread_count = len(unread[0].split()) if unread[0] else 0
                    return ToolResult(
                        success=True,
                        data=f"Gmail Inbox for {addr}: {unread_count} unread messages.",
                        metadata={"unread_count": unread_count, "account": addr}
                    )

            else:
                return ToolResult(success=False, error=f"Unknown Gmail action: '{action}'")

        except Exception as e:
            logger.error(f"Gmail action failed ({action}): {e}")
            return ToolResult(success=False, error=f"Gmail operation error: {str(e)}")
