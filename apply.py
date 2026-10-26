# internship_bot/apply.py
"""Módulo responsável por aplicar automaticamente a vagas na Gupy, Catho e portais com login universal."""

import os
import time
import logging
from pathlib import Path
from typing import Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _setup_driver() -> webdriver.Chrome:
    """Inicializa o ChromeDriver em modo headless com configurações completas."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)


def _handle_portal_login_if_needed(driver: webdriver.Chrome, email: str, password: str) -> None:
    """Tenta autenticar com Google ou formulário de login direto caso apareça tela de identificação."""
    if not email or not password:
        return

    # 1. Tenta botão "Entrar com Google"
    google_btn_selectors = [
        "//button[contains(., 'Google') or contains(., 'google')]",
        "//a[contains(., 'Google') or contains(., 'google')]",
        "button[data-testid*='google']",
        "div[data-provider='google']"
    ]

    for sel in google_btn_selectors:
        try:
            if sel.startswith("//"):
                btns = driver.find_elements(By.XPATH, sel)
            else:
                btns = driver.find_elements(By.CSS_SELECTOR, sel)

            for btn in btns:
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(3)
                    handles = driver.window_handles
                    if len(handles) > 1:
                        driver.switch_to.window(handles[-1])

                    try:
                        g_email = driver.find_elements(By.CSS_SELECTOR, "input[type='email'], input#identifierId")
                        if g_email:
                            g_email[0].send_keys(email + Keys.ENTER)
                            time.sleep(3)
                    except Exception:
                        pass

                    try:
                        g_pass = driver.find_elements(By.CSS_SELECTOR, "input[type='password'], input[name='Passwd']")
                        if g_pass:
                            g_pass[0].send_keys(password + Keys.ENTER)
                            time.sleep(4)
                    except Exception:
                        pass

                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[0])
                    return
        except Exception:
            pass

    # 2. Tenta formulário de login direto (Email / Senha) do portal
    try:
        login_user = driver.find_elements(By.CSS_SELECTOR, "input[name*='login'], input[id*='login'], input[type='email'], input[name='email']")
        login_pass = driver.find_elements(By.CSS_SELECTOR, "input[type='password'], input[name*='password'], input[id*='password']")
        if login_user and login_pass and login_user[0].is_displayed() and login_pass[0].is_displayed():
            login_user[0].clear()
            login_user[0].send_keys(email)
            login_pass[0].clear()
            login_pass[0].send_keys(password)
            submit_btn = driver.find_elements(By.XPATH, "//button[@type='submit' or contains(., 'Entrar') or contains(., 'Acessar')]")
            if submit_btn and submit_btn[0].is_displayed():
                submit_btn[0].click()
                time.sleep(3)
    except Exception:
        pass


def apply_to_vacancy(vacancy: Dict[str, str], cfg: Dict) -> Dict[str, str]:
    """Navega na vaga, efetua login unificado ou preenche os dados do candidato e submete a candidatura."""
    driver = None
    personal = cfg.get("personal", {})
    name = personal.get("name", "")
    email = personal.get("email", "vasconcelosubazzy@gmail.com")
    phone = personal.get("phone", "")
    github = personal.get("github", "")
    city = personal.get("city", "")

    # Senha unificada da plataforma
    password = cfg.get("platforms", {}).get("gupy", {}).get("password", "Fazeclan10-")

    resume_str = cfg.get("resume_path", "./curriculo.pdf")
    resume_path = Path(resume_str).expanduser().resolve()

    try:
        driver = _setup_driver()
        driver.set_page_load_timeout(30)
        logging.info(f"Acessando vaga: {vacancy.get('title')} - {vacancy.get('link')}")
        driver.get(vacancy["link"])
        time.sleep(3)

        # 1. Tenta clicar em botões de candidatura
        apply_button_xpaths = [
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'candidatar')]",
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'candidatar')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'inscreva')]",
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'inscreva')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'participar')]",
        ]

        for xpath in apply_button_xpaths:
            try:
                btns = driver.find_elements(By.XPATH, xpath)
                for btn in btns:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(2)
                        break
            except Exception:
                pass

        # 2. Login universal nos portais se solicitado
        _handle_portal_login_if_needed(driver, email, password)

        # 3. Localiza e preenche campos de formulário caso existam
        filled_any = False

        # Nome
        for selector in ["input[name*='name']", "input[id*='name']", "input[placeholder*='Nome']", "input[name*='nome']"]:
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in inputs:
                    if el.is_displayed() and not el.get_attribute("value"):
                        el.send_keys(name)
                        filled_any = True
            except Exception:
                pass

        # Email
        for selector in ["input[type='email']", "input[name*='email']", "input[id*='email']", "input[placeholder*='mail']"]:
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in inputs:
                    if el.is_displayed() and not el.get_attribute("value"):
                        el.send_keys(email)
                        filled_any = True
            except Exception:
                pass

        # Telefone
        for selector in ["input[type='tel']", "input[name*='phone']", "input[name*='tel']", "input[placeholder*='Telefone']", "input[placeholder*='Celular']"]:
            try:
                inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in inputs:
                    if el.is_displayed() and not el.get_attribute("value"):
                        el.send_keys(phone)
                        filled_any = True
            except Exception:
                pass

        # Cidade
        if city:
            for selector in ["input[name*='city']", "input[name*='cidade']", "input[placeholder*='Cidade']"]:
                try:
                    inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in inputs:
                        if el.is_displayed() and not el.get_attribute("value"):
                            el.send_keys(city)
                            filled_any = True
                except Exception:
                    pass

        # GitHub
        if github:
            for selector in ["input[name*='github']", "input[name*='portfolio']", "input[placeholder*='github']"]:
                try:
                    inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in inputs:
                        if el.is_displayed() and not el.get_attribute("value"):
                            el.send_keys(github)
                            filled_any = True
                except Exception:
                    pass

        # Upload de Currículo
        if resume_path.exists():
            try:
                file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                for finput in file_inputs:
                    finput.send_keys(str(resume_path))
                    filled_any = True
                    logging.info(f"Currículo anexado para: {vacancy.get('title')}")
            except Exception:
                pass

        # 4. Tenta submeter formulário se campos foram preenchidos
        if filled_any:
            submit_selectors = [
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'enviar')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'finalizar')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirmar')]"
            ]
            for s_xpath in submit_selectors:
                try:
                    s_btns = driver.find_elements(By.XPATH, s_xpath)
                    for s_btn in s_btns:
                        if s_btn.is_displayed() and s_btn.is_enabled():
                            driver.execute_script("arguments[0].click();", s_btn)
                            time.sleep(3)
                            logging.info(f"Candidatura submetida para: {vacancy.get('title')}")
                            return {"status": "success", "message": "Formulário preenchido e submetido!"}
                except Exception:
                    pass

            return {"status": "applied_form", "message": "Dados preenchidos automaticamente na vaga."}
        else:
            return {"status": "manual_required", "message": "Vaga exige etapas personalizadas ou testes específicos."}

    except Exception as e:
        logging.error(f"Erro ao processar vaga {vacancy.get('title')}: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
