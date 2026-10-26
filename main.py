# internship_bot/main.py
"""Ponto de entrada principal do Bot de Vagas de Estágio Multiplataforma (LinkedIn, Gupy, Catho)."""

import os
import sys
import yaml
import time
import logging
from typing import Dict

# Suporte a execução direta ou como pacote
try:
    from .scraper import fetch_vacancies
    from .db import (
        init_db,
        insert_vacancy,
        get_unprocessed_vacancies,
        update_vacancy_application,
        mark_vacancy_notified,
    )
    from .notifier import send_email_notification
    from .apply import apply_to_vacancy, _setup_driver
    from .linkedin_bot import run_linkedin_easy_apply
except ImportError:
    from scraper import fetch_vacancies
    from db import (
        init_db,
        insert_vacancy,
        get_unprocessed_vacancies,
        update_vacancy_application,
        mark_vacancy_notified,
    )
    from notifier import send_email_notification
    from apply import apply_to_vacancy, _setup_driver
    from linkedin_bot import run_linkedin_easy_apply

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_config(config_path: str = "config.yaml") -> Dict:
    """Carrega o arquivo YAML de configuração."""
    if not os.path.exists(config_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        alt_path = os.path.join(script_dir, config_path)
        if os.path.exists(alt_path):
            config_path = alt_path

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def main() -> None:
    cfg = load_config()
    db_path = cfg.get("database", "vacancies.db")
    init_db(db_path)

    all_results = []

    # =========================================================================
    # 1️⃣ GUPY, CATHO E PORTAIS DE VAGAS
    # =========================================================================
    feed_urls = []
    gupy_url = cfg.get("platforms", {}).get("gupy", {}).get("rss_url")
    if gupy_url:
        feed_urls.append(("Gupy", gupy_url))

    catho_url = cfg.get("platforms", {}).get("catho_and_portals", {}).get("rss_url")
    if catho_url:
        feed_urls.append(("Catho/Portais", catho_url))

    for source_name, url in feed_urls:
        logging.info(f"Buscando vagas em [{source_name}]...")
        vacancies = fetch_vacancies(url)
        logging.info(f"Obtidas {len(vacancies)} vagas de [{source_name}].")
        for vac in vacancies:
            insert_vacancy(db_path, vac["id"], vac["title"], vac["link"])

    # Recupera vagas pendentes de portais externos
    pending = get_unprocessed_vacancies(db_path)
    if pending:
        logging.info(f"Processando auto-candidatura para {len(pending)} vagas de portais...")
        for vac in pending:
            res = apply_to_vacancy(vac, cfg)
            status_flag = 1 if res.get("status") in ["success", "applied_form"] else 0
            update_vacancy_application(db_path, vac["id"], status_flag, res.get("status", "unknown"))
            all_results.append({
                "source": "Gupy/Portais",
                "title": vac["title"],
                "link": vac["link"],
                "status": res.get("status"),
                "message": res.get("message"),
            })
            mark_vacancy_notified(db_path, vac["id"])
            time.sleep(2)

    # =========================================================================
    # 2️⃣ LINKEDIN (Candidatura Simplificada / Easy Apply)
    # =========================================================================
    linkedin_cfg = cfg.get("platforms", {}).get("linkedin", {})
    if linkedin_cfg.get("enabled", True):
        driver = None
        try:
            driver = _setup_driver()
            linkedin_results = run_linkedin_easy_apply(driver, cfg)
            for li_item in linkedin_results:
                insert_vacancy(db_path, li_item["id"], li_item["title"], li_item["link"])
                update_vacancy_application(db_path, li_item["id"], 1 if li_item["status"] == "success" else 0, li_item["status"])
                mark_vacancy_notified(db_path, li_item["id"])
                all_results.append({
                    "source": "LinkedIn",
                    "title": li_item["title"],
                    "link": li_item["link"],
                    "status": li_item["status"],
                    "message": li_item["message"],
                })
        except Exception as li_err:
            logging.error(f"Erro no módulo LinkedIn: {li_err}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    # =========================================================================
    # 3️⃣ ENVIO DE RELATÓRIO POR E-MAIL
    # =========================================================================
    if not all_results:
        logging.info("Nenhuma nova vaga encontrada nesta rodada.")
        return

    candidate_name = cfg.get("personal", {}).get("name", "Alexsandro")
    lines = [
        f"Olá {candidate_name},\n",
        f"O seu Bot Multiplataforma processou {len(all_results)} vaga(s) nesta rodada (LinkedIn, Gupy, Catho):\n",
        "=" * 60 + "\n"
    ]

    for item in all_results:
        status_icon = "✅ Candidatura Enviada" if item["status"] == "success" else (
            "📝 Formulário Preenchido" if item["status"] == "applied_form" else "ℹ️ Link para Candidatura"
        )
        lines.append(f"📌 [{item['source']}] {item['title']}")
        lines.append(f"Status: {status_icon} ({item['message']})")
        lines.append(f"🔗 {item['link']}\n")

    message = "\n".join(lines)

    email_cfg = cfg.get("email")
    if email_cfg and email_cfg.get("user") and email_cfg.get("password"):
        send_email_notification(email_cfg, message)
        logging.info("Relatório multiplataforma enviado com sucesso por e-mail.")

    logging.info("Ciclo concluído com sucesso.")


if __name__ == "__main__":
    cfg = load_config()
    interval = cfg.get("schedule", {}).get("interval_minutes", 60)
    logging.info("Iniciando Bot de Estágios Multiplataforma (LinkedIn, Gupy, Catho)...")
    while True:
        try:
            main()
        except Exception as e:
            logging.error(f"Erro durante a execução: {e}")

        logging.info(f"Aguardando {interval} minutos para a próxima verificação...")
        time.sleep(interval * 60)
