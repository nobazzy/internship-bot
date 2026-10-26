# internship_bot/linkedin_bot.py
"""Módulo de automação do LinkedIn com filtro estrito de TI e vagas recentes (até 14 dias)."""

import os
import time
import urllib.parse
import logging
from pathlib import Path
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from .scraper import is_strictly_tech_internship
except ImportError:
    from scraper import is_strictly_tech_internship


def login_linkedin(driver: webdriver.Chrome, email: str, password: str) -> bool:
    """Realiza o login na conta do LinkedIn com seletores resilientes."""
    try:
        logging.info("Acessando tela de login do LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(3)

        if "feed" in driver.current_url or "checkpoint" in driver.current_url:
            return True

        user_input = None
        for sel in ["#username", "#session_key", "input[name='session_key']", "input[type='text']"]:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                if els and els[0].is_displayed():
                    user_input = els[0]
                    break
            except Exception:
                pass

        pass_input = None
        for sel in ["#password", "#session_password", "input[name='session_password']", "input[type='password']"]:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                if els and els[0].is_displayed():
                    pass_input = els[0]
                    break
            except Exception:
                pass

        if not user_input or not pass_input:
            logging.warning("Campos de login do LinkedIn não encontrados.")
            return False

        user_input.clear()
        user_input.send_keys(email)
        pass_input.clear()
        pass_input.send_keys(password)

        submit_btns = driver.find_elements(By.XPATH, "//button[@type='submit' or contains(., 'Entrar') or contains(., 'Sign in')]")
        if submit_btns:
            submit_btns[0].click()
        else:
            pass_input.send_keys(Keys.ENTER)

        time.sleep(5)

        if "login" not in driver.current_url:
            logging.info("Login no LinkedIn realizado com sucesso!")
            return True
        else:
            logging.warning("Verificação adicional ou erro de credenciais no LinkedIn.")
            return False
    except Exception as e:
        logging.error(f"Erro durante login no LinkedIn: {e}")
        return False


def run_linkedin_easy_apply(driver: webdriver.Chrome, cfg: Dict) -> List[Dict]:
    """Busca vagas com Candidatura Simplificada no LinkedIn focadas em TI e postadas em até 14 dias."""
    linkedin_cfg = cfg.get("platforms", {}).get("linkedin", {})
    if not linkedin_cfg.get("enabled", True):
        return []

    username = linkedin_cfg.get("username", "")
    password = linkedin_cfg.get("password", "")

    if not username or not password:
        logging.warning("Credenciais do LinkedIn não informadas no config.yaml.")
        return []

    logged_in = login_linkedin(driver, username, password)
    if not logged_in:
        logging.warning("Não foi possível autenticar no LinkedIn no momento.")
        return []

    personal = cfg.get("personal", {})
    phone = personal.get("phone", "11935855321")
    resume_path = Path(cfg.get("resume_path", "./curriculo.pdf")).expanduser().resolve()

    keywords = linkedin_cfg.get("keywords", ["Estágio TI", "Estágio Java", "Estágio Python", "Estágio Desenvolvimento"])
    location = linkedin_cfg.get("location", "São Paulo, Brasil")

    results = []

    for kw in keywords:
        logging.info(f"Buscando vagas de TI (últimas 2 semanas) no LinkedIn para: '{kw}'...")
        encoded_kw = urllib.parse.quote(kw)
        encoded_loc = urllib.parse.quote(location)
        # f_AL=true -> Easy Apply | f_E=1 -> Internship | f_TPR=r1209600 -> Últimas 2 semanas (14 dias)
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_kw}&location={encoded_loc}&f_AL=true&f_E=1&f_TPR=r1209600"

        try:
            driver.get(search_url)
            time.sleep(3)

            job_cards = driver.find_elements(By.CSS_SELECTOR, "li.jobs-search-results__list-item, div.job-card-container, div.base-card")
            logging.info(f"Encontrados {len(job_cards)} cartões de vagas no LinkedIn para '{kw}'.")

            for card in job_cards[:5]:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", card)
                    time.sleep(1)
                    card.click()
                    time.sleep(2)

                    title = "Vaga LinkedIn"
                    try:
                        title_el = driver.find_element(By.CSS_SELECTOR, "h2.job-details-jobs-unified-top-card__job-title, h1.t-24, h2.topcard__title")
                        title = title_el.text.strip()
                    except Exception:
                        pass

                    # Filtro de pertinência a TI
                    if not is_strictly_tech_internship(title):
                        logging.info(f"Vaga '{title}' descartada por não ser estritamente de TI.")
                        continue

                    job_link = driver.current_url

                    apply_btn = None
                    for btn_selector in [
                        "button.jobs-apply-button",
                        "//button[contains(., 'Candidatura simplificada')]",
                        "//button[contains(., 'Easy Apply')]"
                    ]:
                        try:
                            if btn_selector.startswith("//"):
                                found = driver.find_elements(By.XPATH, btn_selector)
                            else:
                                found = driver.find_elements(By.CSS_SELECTOR, btn_selector)
                            if found and found[0].is_displayed():
                                apply_btn = found[0]
                                break
                        except Exception:
                            pass

                    if not apply_btn:
                        continue

                    apply_btn.click()
                    time.sleep(2)

                    applied_success = False
                    for step in range(5):
                        try:
                            phone_inputs = driver.find_elements(By.CSS_SELECTOR, "input[id*='phoneNumber'], input[name*='phoneNumber']")
                            for p_in in phone_inputs:
                                if p_in.is_displayed() and not p_in.get_attribute("value"):
                                    p_in.send_keys(phone)
                        except Exception:
                            pass

                        if resume_path.exists():
                            try:
                                file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                                for fi in file_inputs:
                                    fi.send_keys(str(resume_path))
                            except Exception:
                                pass

                        submit_final = driver.find_elements(By.XPATH, "//button[contains(., 'Enviar candidatura') or contains(., 'Submit application')]")
                        if submit_final and submit_final[0].is_displayed():
                            submit_final[0].click()
                            time.sleep(3)
                            applied_success = True
                            logging.info(f"✅ Candidatura enviada com sucesso no LinkedIn para: {title}")
                            break

                        next_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Avançar') or contains(., 'Next') or contains(., 'Revisar') or contains(., 'Review')]")
                        if next_btns and next_btns[0].is_displayed():
                            next_btns[0].click()
                            time.sleep(2)
                        else:
                            break

                    status = "success" if applied_success else "applied_form"
                    msg = "Candidatura Simplificada enviada via LinkedIn!" if applied_success else "Etapas do LinkedIn preenchidas."
                    results.append({
                        "id": f"linkedin_{int(time.time()*1000)}",
                        "title": f"[LinkedIn] {title}",
                        "link": job_link,
                        "status": status,
                        "message": msg
                    })

                    try:
                        dismiss_btn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Fechar'], button[aria-label*='Dismiss']")
                        if dismiss_btn:
                            dismiss_btn[0].click()
                            time.sleep(1)
                            discard_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Descartar') or contains(., 'Discard')]")
                            if discard_btn:
                                discard_btn[0].click()
                    except Exception:
                        pass

                except Exception as card_err:
                    logging.debug(f"Erro ao interagir com cartão de vaga LinkedIn: {card_err}")

        except Exception as kw_err:
            logging.error(f"Erro na busca do LinkedIn para '{kw}': {kw_err}")

    return results
