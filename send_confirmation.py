# internship_bot/send_confirmation.py
"""Gera e envia o e-mail de confirmação com todas as candidaturas registradas."""

import sqlite3
import yaml
import logging
from datetime import datetime
from notifier import send_email_notification

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def send_confirmation_report():
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    db_path = cfg.get("database", "vacancies.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT title, link, apply_status FROM vacancies WHERE applied = 1 ORDER BY rowid DESC")
    applied_rows = cur.fetchall()
    conn.close()

    total_applied = len(applied_rows)
    candidate_name = cfg.get("personal", {}).get("name", "Alexsandro Vasconcelos")
    now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # Plain text version
    lines = [
        f"Olá {candidate_name},\n",
        f"Segue a confirmação das suas candidaturas automáticas de estágio realizadas pelo bot.\n",
        f"Data/Hora do Relatório: {now_str}",
        f"Total de Candidaturas Enviadas: {total_applied}\n",
        "=" * 60 + "\n"
    ]

    for r in applied_rows:
        lines.append(f"📌 {r[0]}")
        lines.append(f"Status: ✅ Candidatura Enviada com Sucesso")
        lines.append(f"🔗 Link da Vaga: {r[1]}\n")

    text_body = "\n".join(lines)

    # HTML Version
    table_rows = ""
    for r in applied_rows:
        table_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px 16px; font-weight: 500; color: #1e293b;">{r[0]}</td>
            <td style="padding: 12px 16px; text-align: center;">
                <span style="background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600;">
                    ✓ Enviada
                </span>
            </td>
            <td style="padding: 12px 16px; text-align: center;">
                <a href="{r[1]}" style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500;">
                    Ver Vaga
                </a>
            </td>
        </tr>
        """

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px;">
        <div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 28px 32px; color: #ffffff;">
                <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700;">🚀 Confirmação de Candidaturas de Estágio</h1>
                <p style="margin: 0; font-size: 14px; opacity: 0.9;">Relatório de vagas aplicadas automaticamente para <strong>{candidate_name}</strong></p>
            </div>
            
            <div style="padding: 24px 32px;">
                <div style="display: flex; justify-content: space-between; background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 14px 20px; margin-bottom: 24px;">
                    <div>
                        <span style="font-size: 12px; color: #1e40af; font-weight: 600; text-transform: uppercase;">Total Aplicado</span>
                        <div style="font-size: 20px; font-weight: 700; color: #1e3a8a;">{total_applied} vagas</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 12px; color: #1e40af; font-weight: 600; text-transform: uppercase;">Data de Envio</span>
                        <div style="font-size: 14px; font-weight: 600; color: #1e3a8a; margin-top: 4px;">{now_str}</div>
                    </div>
                </div>

                <h2 style="font-size: 16px; font-weight: 600; color: #334155; margin: 0 0 16px 0;">Vagas com Candidatura Confirmada:</h2>
                
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                    <thead>
                        <tr style="background-color: #f1f5f9; color: #475569; font-size: 12px; text-transform: uppercase;">
                            <th style="padding: 10px 16px; border-top-left-radius: 6px;">Título da Vaga</th>
                            <th style="padding: 10px 16px; text-align: center;">Status</th>
                            <th style="padding: 10px 16px; text-align: center; border-top-right-radius: 6px;">Link</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>

            <div style="background-color: #f8fafc; padding: 16px 32px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center;">
                Este é um e-mail automático gerado pelo seu Bot de Estágios.
            </div>
        </div>
    </body>
    </html>
    """

    email_cfg = cfg.get("email", {})
    send_email_notification(email_cfg, text_body, html_body)


if __name__ == "__main__":
    send_confirmation_report()
