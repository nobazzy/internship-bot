# internship_bot/scraper.py
"""Scraper de vagas de estágio com filtros estritos: TI + Últimos 14 dias + SP / Remoto."""

import os
import certifi
import feedparser
import logging
import unicodedata
from datetime import datetime, timedelta
from time import mktime
from typing import List, Dict

# Garante certificado SSL correto no Windows
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()

# Palavras-chave de TI
TECH_KEYWORDS = [
    "ti", "t.i", "tecnologia", "computacao", "desenvolvimento", "desenvolvedor",
    "software", "java", "python", "banco de dados", "sql", "suporte", "analise de sistemas",
    "programacao", "programador", "web", "frontend", "backend", "full stack", "fullstack",
    "dados", "qa", "devops", "cloud", "infraestrutura", "redes", "seguranca da informacao"
]

# Áreas bloqueadas (não-TI)
EXCLUDED_KEYWORDS = [
    "contabilidade", "contabil", "farmacia", "farmaceutica", "direito", "advocacia",
    "logistica", "recursos humanos", "rh", "psicologia", "enfermagem", "medicina",
    "ensino medio", "pedagogia", "nutricao", "engenharia civil", "quimica", "recepcionista",
    "secretariado", "letras", "biomedicina", "odontologia", "arquitetura", "gastronomia"
]

# Localizações aceitas (São Paulo, Região Metropolitana, Alto Tietê ou Remoto)
ACCEPTED_LOCATIONS = [
    "sao paulo", "sp", "itaquaquecetuba", "mogi das cruzes", "suzano", "guarulhos",
    "poa", "ferraz", "aruja", "santo andre", "sao bernardo", "sao caetano", "diadema",
    "osasco", "barueri", "alphaville", "campinas", "santos", "jundiai", "sorocaba",
    "sao jose dos campos", "remoto", "home office", "teletrabalho", "hibrido", "hibrida"
]

# Outros estados/cidades bloqueados (quando não forem remotos)
OTHER_STATES = [
    "rio de janeiro", "/ rj", "- rj", "salvador", "/ ba", "- ba", "bahia",
    "recife", "/ pe", "- pe", "pernambuco", "brasilia", "/ df", "- df",
    "curitiba", "/ pr", "- pr", "parana", "porto alegre", "/ rs", "- rs",
    "belo horizonte", "/ mg", "- mg", "minas gerais", "fortaleza", "/ ce", "- ce",
    "goiania", "/ go", "- go", "manaus", "/ am", "- am", "paraiba", "/ pb", "- pb",
    "florianopolis", "/ sc", "- sc", "vitoria", "/ es", "- es", "natal", "/ rn", "- rn",
    "maceio", "/ al", "- al", "serra /", "guarapari"
]


def normalize_text(text: str) -> str:
    """Remove acentuação e converte para minúsculas."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def is_sp_or_remote(title: str) -> bool:
    """Verifica se a vaga é em São Paulo (SP) ou Remoto/Home Office."""
    clean_title = normalize_text(title)

    # Se for explicitamente remoto / home office, aceita sempre
    if any(rem in clean_title for rem in ["remoto", "home office", "teletrabalho"]):
        return True

    # Se indicar outro estado explicitamente, rejeita
    for other in OTHER_STATES:
        if other in clean_title:
            return False

    # Verifica se contém indicação de SP ou cidades da região
    return any(loc in clean_title for loc in ACCEPTED_LOCATIONS)


def is_strictly_tech_internship(title: str) -> bool:
    """Verifica se a vaga é estritamente TI / Estágio."""
    clean_title = normalize_text(title)

    for excl in EXCLUDED_KEYWORDS:
        if excl in clean_title:
            if not any(k in clean_title for k in ["ti", "t.i", "software", "computacao", "desenvolvimento"]):
                return False

    has_tech = any(kw in clean_title for kw in TECH_KEYWORDS)
    is_entry_level = any(lvl in clean_title for lvl in ["estagio", "estagiario", "trainee", "junior", "jr", "inicial", "assistente ti"])

    return has_tech and is_entry_level


def is_within_last_14_days(entry_parsed_time) -> bool:
    """Verifica se a vaga foi publicada nos últimos 14 dias."""
    if not entry_parsed_time:
        return True
    now = datetime.now()
    fourteen_days_ago = now - timedelta(days=14)
    try:
        pub_dt = datetime.fromtimestamp(mktime(entry_parsed_time))
        return pub_dt >= fourteen_days_ago
    except Exception:
        return True


def fetch_vacancies(rss_url: str) -> List[Dict[str, str]]:
    """Busca vagas aplicando a tríade de filtros: TI + Últimos 14 dias + SP/Remoto."""
    try:
        feed = feedparser.parse(rss_url)
        vacancies: List[Dict[str, str]] = []

        for entry in feed.entries:
            title = entry.title

            # 1. Filtro de Área: TI / Estágio
            if not is_strictly_tech_internship(title):
                continue

            # 2. Filtro de Localização: São Paulo / Remoto
            if not is_sp_or_remote(title):
                continue

            # 3. Filtro de Data: até 14 dias
            pub_parsed = getattr(entry, "published_parsed", getattr(entry, "updated_parsed", None))
            if not is_within_last_14_days(pub_parsed):
                continue

            vac_id = getattr(entry, "guid", getattr(entry, "id", entry.link))
            vacancies.append({
                "id": str(vac_id),
                "title": title,
                "link": entry.link,
                "published": getattr(entry, "published", "Recente (SP/Remoto)")
            })

        logging.info(f"Filtro estrito (TI + SP/Remoto + 14 dias): {len(vacancies)} vagas selecionadas.")
        return vacancies
    except Exception as e:
        logging.error(f"Erro ao buscar vagas do feed {rss_url}: {e}")
        return []
