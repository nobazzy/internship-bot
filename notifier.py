# internship_bot/notifier.py
"""Módulo de envio de e-mails de confirmação e relatórios de candidaturas."""

import smtplib
import logging
from email.message import EmailMessage
from typing import Dict, List, Union


def send_email_notification(email_cfg: Dict, message_body: str, html_body: str = None) -> bool:
    """Envia e-mail formatado para um ou mais destinatários."""
    user = email_cfg.get("user")
    password = email_cfg.get("password")
    smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port = email_cfg.get("smtp_port", 465)
    to_email = email_cfg.get("to_email", user)

    # Suporta lista de destinatários ou string separada por vírgula
    if isinstance(to_email, list):
        recipients = to_email
    elif isinstance(to_email, str):
        recipients = [e.strip() for e in to_email.split(",") if e.strip()]
    else:
        recipients = [user]

    if not user or not password:
        logging.warning("Credenciais de e-mail não configuradas.")
        return False

    msg = EmailMessage()
    msg["Subject"] = "🚀 Confirmação de Candidaturas - Bot de Estágios"
    msg["From"] = f"Bot de Estágios <{user}>"
    msg["To"] = ", ".join(recipients)
    msg.set_content(message_body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)

        logging.info(f"E-mail de confirmação enviado com sucesso para: {', '.join(recipients)}!")
        return True
    except Exception as e:
        logging.error(f"Erro ao enviar e-mail: {e}")
        return False
