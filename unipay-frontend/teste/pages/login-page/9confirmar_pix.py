import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fixos import EMAIL_DESTINO, EMAIL_TESTE, NOME_DESTINO, SENHA_TESTE


def ler_saldo(navegador):
    saldo_texto = navegador.find_element(By.ID, "available-balance").text
    saldo_texto = saldo_texto.replace("R$", "").replace("\xa0", "").replace(" ", "")
    saldo_texto = saldo_texto.replace(".", "").replace(",", ".")
    return float(saldo_texto)


def capturar_tela(navegador, resultado):
    # Aqui fica a pasta das prints desse teste.
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "9confirmar_pix"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    # Pego a data e a hora pra não repetir o nome da print.
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    caminho_imagem = pasta_raiz / f"9confirmar_pix_{resultado}_{data_hora}.png"

    # Tiro uma print pra mostrar o resultado.
    imagem_salva = navegador.save_screenshot(str(caminho_imagem))
    if imagem_salva:
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_ct09_confirmar_pix():
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

        # Espero voltar pro login e entro com a conta principal de teste.
        WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "login-email"))
        )
        campo_login = navegador.find_element(By.ID, "login-email")
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

        # Abro o PIX, coloco a chave e confiro o valor.
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
        destinatario_confirmacao = navegador.find_element(By.CSS_SELECTOR, ".recipient-pill strong").text
        chave_confirmacao = navegador.find_element(By.CSS_SELECTOR, ".recipient-pill small:last-child").text
        assert destinatario_confirmacao == nome_destinatario
        assert chave_confirmacao == email_destinatario

        campo_valor.send_keys("10,00")
        time.sleep(1)
        assert campo_valor.get_attribute("value") == "10,00"

        # Confirmo o PIX e espero aparecer que deu certo.
        mensagens_erro = navegador.find_elements(By.CSS_SELECTOR, "[role='alert']")
        assert len(mensagens_erro) == 0
        navegador.find_element(By.ID, "pix-confirm").click()

        comprovante = WebDriverWait(navegador, 15).until(
            EC.visibility_of_element_located((By.ID, "pix-transfer-success"))
        )
        valor_concluido = navegador.find_element(By.ID, "pix-success-amount").text.replace("\xa0", " ")
        destinatario_concluido = navegador.find_element(By.ID, "pix-success-recipient").text
        assert comprovante.is_displayed()
        assert "PIX REALIZADO" in comprovante.text
        assert email_destinatario == destinatario_concluido
        assert "R$" in valor_concluido and "10,00" in valor_concluido
        assert len(navegador.find_elements(By.CSS_SELECTOR, "[role='alert']")) == 0

        # Salvo a print da confirmação.
        capturar_tela(navegador, "sucesso")

        # Volto pro início e confiro se os R$ 10,00 foram descontados.
        navegador.find_element(By.ID, "pix-finish").click()
        WebDriverWait(navegador, 10).until(
            lambda driver: abs(ler_saldo(driver) - (saldo_inicial - 10)) < 0.01
        )
        assert abs(ler_saldo(navegador) - (saldo_inicial - 10)) < 0.01

    except Exception:
        # Se der erro, também salvo uma print.
        capturar_tela(navegador, "falha")
        raise

    finally:
        print("\nO navegador será fechado em 5 segundos...")
        time.sleep(5)
        navegador.quit()


if __name__ == "__main__":
    test_ct09_confirmar_pix()
