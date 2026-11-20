import re
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fixos import CPF_DESTINO, EMAIL_DESTINO, EMAIL_TESTE, NOME_DESTINO, SENHA_TESTE


def formatar_cpf(cpf):
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def ler_saldo(navegador):
    saldo_texto = navegador.find_element(By.ID, "available-balance").text
    saldo_texto = saldo_texto.replace("R$", "").replace("\xa0", "").replace(" ", "")
    saldo_texto = saldo_texto.replace(".", "").replace(",", ".")
    return float(saldo_texto)


def capturar_tela(navegador, resultado):
    # Aqui fica a pasta das prints desse teste.
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "10detalhes_transacao_pix"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    caminho_imagem = pasta_raiz / f"10detalhes_transacao_pix_{resultado}_{data_hora}.png"
    imagem_salva = navegador.save_screenshot(str(caminho_imagem))
    if imagem_salva:
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_ct10_detalhes_transacao_pix():
    opcoes = webdriver.ChromeOptions()
    opcoes.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    navegador = webdriver.Chrome(options=opcoes)

    try:
        navegador.maximize_window()

        # Uso a conta de destino que já está no seed.
        navegador.get("http://localhost:8080/")
        time.sleep(2)
        email_destinatario = EMAIL_DESTINO
        nome_destinatario = NOME_DESTINO
        cpf_destinatario = CPF_DESTINO

        # Espero voltar pro login e entro com a conta principal de teste.
        campo_login = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "login-email"))
        )
        campo_login.clear()
        campo_login.send_keys(EMAIL_TESTE)
        time.sleep(1)
        navegador.find_element(By.ID, "login-password").send_keys(SENHA_TESTE)
        time.sleep(1)
        navegador.find_element(By.ID, "login-submit").click()
        time.sleep(1)

        titulo_menu = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "side-label"))
        )
        assert titulo_menu.text == "MENU"

        # Se faltar saldo, faço um depósito pra conseguir testar o PIX.
        saldo_inicial = ler_saldo(navegador)
        if saldo_inicial <= 10:
            navegador.find_element(By.ID, "open-deposit").click()
            time.sleep(1)
            navegador.find_element(By.ID, "deposit-amount").send_keys("50.00")
            time.sleep(1)
            navegador.find_element(By.ID, "confirm-deposit").click()
            WebDriverWait(navegador, 10).until(lambda driver: ler_saldo(driver) > 10)
            saldo_inicial = ler_saldo(navegador)
        assert saldo_inicial > 10

        # Faço um PIX de R$ 10,00 e guardo os dados pra conferir depois.
        navegador.find_element(By.ID, "make-pix").click()
        time.sleep(1)
        campo_chave = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "pix-recipient-key"))
        )
        campo_chave.send_keys(email_destinatario)
        time.sleep(1)
        navegador.find_element(By.ID, "pix-next-key").click()
        time.sleep(1)

        campo_valor = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "pix-amount-input"))
        )
        assert navegador.find_element(By.CSS_SELECTOR, ".recipient-pill strong").text == nome_destinatario
        assert navegador.find_element(By.CSS_SELECTOR, ".recipient-pill small:last-child").text == email_destinatario
        campo_valor.send_keys("10,00")
        time.sleep(1)
        assert campo_valor.get_attribute("value") == "10,00"

        valor_transferencia = "10,00"
        data_hora_execucao = datetime.now()
        navegador.find_element(By.ID, "pix-confirm").click()
        time.sleep(1)
        WebDriverWait(navegador, 15).until(
            EC.visibility_of_element_located((By.ID, "pix-transfer-success"))
        )

        # Volto pro início e abro o PIX que acabei de fazer.
        navegador.find_element(By.ID, "pix-finish").click()
        time.sleep(1)
        WebDriverWait(navegador, 10).until(
            lambda driver: abs(ler_saldo(driver) - (saldo_inicial - 10)) < 0.01
        )
        transacao = WebDriverWait(navegador, 15).until(
            lambda driver: next(
                (item for item in driver.find_elements(By.CSS_SELECTOR, "button.transaction")
                 if item.is_displayed() and nome_destinatario in item.text and valor_transferencia in item.text),
                False,
            )
        )
        transacao.click()

        # Confiro os dados que aparecem nos detalhes da movimentação.
        drawer = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".transaction-drawer"))
        )
        valor_exibido = navegador.find_element(By.ID, "receipt-amount").text.replace("\xa0", " ")
        destinatario_exibido = navegador.find_element(By.ID, "receipt-recipient").text
        cpf_exibido = navegador.find_element(By.ID, "receipt-cpf").text
        chave_exibida = navegador.find_element(By.ID, "receipt-pix-key").text
        data_hora_exibida = navegador.find_element(By.ID, "receipt-date").text
        status_exibido = navegador.find_element(By.ID, "receipt-status").text

        assert drawer.is_displayed()
        assert "R$" in valor_exibido and valor_transferencia in valor_exibido
        assert destinatario_exibido == nome_destinatario
        assert cpf_exibido == formatar_cpf(cpf_destinatario)
        assert chave_exibida == email_destinatario
        assert status_exibido in ("Concluída", "Realizada", "Aprovada")

        data_hora_match = re.search(
            r"(\d{2}/\d{2}/\d{4})[,\s]+(\d{2}:\d{2}(?::\d{2})?)",
            data_hora_exibida,
        )
        assert data_hora_match, f"Data ou horário em formato inesperado: {data_hora_exibida}"
        data_exibida = datetime.strptime(data_hora_match.group(1), "%d/%m/%Y").date()
        horario_exibido = datetime.strptime(data_hora_match.group(2), "%H:%M:%S" if data_hora_match.group(2).count(":") == 2 else "%H:%M").time()
        assert data_exibida == data_hora_execucao.date()
        horario_transacao = datetime.combine(data_exibida, horario_exibido)
        assert abs((horario_transacao - data_hora_execucao).total_seconds()) <= 5 * 60

        capturar_tela(navegador, "sucesso")

    except Exception:
        capturar_tela(navegador, "falha")
        raise

    finally:
        print("\nO navegador será fechado em 5 segundos...")
        time.sleep(5)
        navegador.quit()


if __name__ == "__main__":
    test_ct10_detalhes_transacao_pix()
