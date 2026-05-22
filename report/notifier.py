"""
report/notifier.py — E-posta / Slack / Teams bildirimi
"""

import logging
import os
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)
NOTIF_PATH = Path("config/notifications.yaml")


class Notifier:
    def __init__(self):
        self.config = self._load()

    def _load(self) -> dict:
        if NOTIF_PATH.exists():
            return yaml.safe_load(NOTIF_PATH.read_text())
        return {}

    def send(self, title: str, body: str, severity: str = "medium",
             pdf_path: str = None):
        channels = self.config.get("alert_levels", {}).get(severity, {}).get("channels", [])
        for channel in channels:
            cfg = self.config.get("channels", {}).get(channel, {})
            if not cfg.get("enabled"):
                continue
            try:
                if channel == "slack":
                    self._slack(cfg, title, body)
                elif channel == "teams":
                    self._teams(cfg, title, body)
                elif channel == "email":
                    self._email(cfg, title, body, pdf_path)
            except Exception as e:
                logger.error(f"Bildirim hatası [{channel}]: {e}")

    def _slack(self, cfg: dict, title: str, body: str):
        import requests
        webhook = cfg.get("webhook_url", "")
        if not webhook:
            return
        requests.post(webhook, json={
            "text": f"*{title}*\n{body[:500]}"
        }, timeout=10)
        logger.info("Slack bildirimi gönderildi.")

    def _teams(self, cfg: dict, title: str, body: str):
        import requests
        webhook = cfg.get("webhook_url", "")
        if not webhook:
            return
        requests.post(webhook, json={
            "@type": "MessageCard",
            "summary": title,
            "title": title,
            "text": body[:1000],
        }, timeout=10)
        logger.info("Teams bildirimi gönderildi.")

    def _email(self, cfg: dict, title: str, body: str, pdf_path: str = None):
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        msg = MIMEMultipart()
        msg["From"] = cfg.get("sender", "")
        msg["To"] = ", ".join(cfg.get("recipients", []))
        msg["Subject"] = f"SENTINEL | {title}"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        if pdf_path and Path(pdf_path).exists():
            with open(pdf_path, "rb") as f:
                attachment = MIMEApplication(f.read(), _subtype="pdf")
                attachment.add_header("Content-Disposition", "attachment",
                                      filename=Path(pdf_path).name)
                msg.attach(attachment)

        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg.get("sender", ""), os.environ.get("SMTP_PASSWORD", ""))
            server.send_message(msg)
        logger.info("E-posta gönderildi.")
