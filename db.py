# internship_bot/db.py
"""Funções de suporte ao banco SQLite com controle de candidaturas."""

import sqlite3
from typing import List, Dict


def init_db(db_path: str) -> None:
    """Cria o arquivo e a tabela de vagas caso ainda não existam."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS vacancies (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            notified INTEGER DEFAULT 0,
            applied INTEGER DEFAULT 0,
            apply_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Garante que colunas novas existam caso o banco seja antigo
    try:
        cur.execute("ALTER TABLE vacancies ADD COLUMN applied INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE vacancies ADD COLUMN apply_status TEXT DEFAULT 'pending'")
    except Exception:
        pass
    conn.commit()
    conn.close()


def insert_vacancy(db_path: str, vac_id: str, title: str, link: str) -> bool:
    """Insere uma nova vaga. Retorna True se for nova, False se já existir."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO vacancies (id, title, link, notified, applied, apply_status) VALUES (?,?,?,0,0,'pending')",
            (vac_id, title, link),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_unprocessed_vacancies(db_path: str) -> List[Dict]:
    """Retorna todas as vagas ainda não notificadas."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, title, link, applied, apply_status FROM vacancies WHERE notified = 0")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "link": r[2], "applied": r[3], "apply_status": r[4]} for r in rows]


def update_vacancy_application(db_path: str, vac_id: str, applied: int, status: str) -> None:
    """Atualiza o status de aplicação da vaga."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE vacancies SET applied = ?, apply_status = ? WHERE id = ?", (applied, status, vac_id))
    conn.commit()
    conn.close()


def mark_vacancy_notified(db_path: str, vac_id: str) -> None:
    """Marca a vaga como notificada."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE vacancies SET notified = 1 WHERE id = ?", (vac_id,))
    conn.commit()
    conn.close()
