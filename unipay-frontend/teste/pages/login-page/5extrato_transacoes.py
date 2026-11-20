import re
import time
from datetime import datetime
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fixos import EMAIL_TESTE, SENHA_TESTE


def ler_saldo(navegador):
    saldo_texto = navegador.find_element(By.ID, "available-balance").text
    saldo_texto = saldo_texto.replace("R$", "").replace("\xa0", "").replace(" ", "")
    saldo_texto = saldo_texto.replace(".", "").replace(",", ".")
    return float(saldo_texto)


def capturar_tela(navegador, resultado):
    # Aqui fica a pasta das prints desse teste.
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "5extrato_transacoes"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    caminho_imagem = pasta_raiz / f"5extrato_transacoes_{resultado}_{data_hora}.png"
    imagem_salva = navegador.save_screenshot(str(caminho_imagem))

    if imagem_salva:
        # Passo a imagem pelo Pillow e salvo a print.
        with Image.open(caminho_imagem) as imagem:
            imagem.convert("RGB").save(caminho_imagem, format="PNG")
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_ct05_extrato_transacoes():
    opcoes = webdriver.ChromeOptions()
    opcoes.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    navegador = webdriver.Chrome(options=opcoes)

    try:
        navegador.maximize_window()
        navegador.get("http://localhost:8080/")

        # Entro com a conta de teste.
        campo_email = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "login-email"))
        )
        campo_email.send_keys(EMAIL_TESTE)
        time.sleep(1)
        navegador.find_element(By.ID, "login-password").send_keys(SENHA_TESTE)
        time.sleep(1)
        navegador.find_element(By.ID, "login-submit").click()
        time.sleep(1)

        menu = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "side-label"))
        )
        assert menu.text == "MENU"

        # O extrato já aparece na página inicial.
        extrato = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "section.statement"))
        )
        assert extrato.is_displayed()

        transacoes = navegador.find_elements(By.CSS_SELECTOR, "button.transaction")
        if len(transacoes) == 0:
            # Se não tiver movimentação, faço um depósito pra aparecer no extrato.
            navegador.find_element(By.ID, "open-deposit").click()
            time.sleep(1)
            navegador.find_element(By.ID, "deposit-amount").send_keys("1.00")
            time.sleep(1)
            navegador.find_element(By.ID, "confirm-deposit").click()
            time.sleep(1)
            WebDriverWait(navegador, 10).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "button.transaction")) > 0
            )
            transacoes = navegador.find_elements(By.CSS_SELECTOR, "button.transaction")

        assert len(transacoes) > 0, "O extrato não possui movimentações para exibir."

        # Confiro se cada movimentação mostra descrição, valor e data.
        for indice, transacao in enumerate(transacoes, start=1):
            texto = transacao.text.replace("\xa0", " ").strip()
            assert texto, f"A transação {indice} está sem conteúdo."
            assert "None" not in texto and "undefined" not in texto, texto

            linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
            assert len(linhas) >= 4, f"A transação {indice} não apresenta todos os dados: {texto}"
            assert "R$" in texto, f"A transação {indice} não apresenta valor em reais: {texto}"
            assert re.search(r"\d{2}/\d{2}/\d{2,4}", texto), (
                f"A transação {indice} não apresenta uma data legível: {texto}"
            )
            assert any(
                marcador in texto.lower()
                for marcador in ("pix", "depósito", "transferência")
            ), f"A transação {indice} não apresenta tipo ou descrição: {texto}"

        capturar_tela(navegador, "sucesso")

    except Exception:
        capturar_tela(navegador, "falha")
        raise

    finally:
        print("\nO navegador será fechado em 5 segundos...")
        time.sleep(5)
        navegador.quit()


if __name__ == "__main__":
    test_ct05_extrato_transacoes()
