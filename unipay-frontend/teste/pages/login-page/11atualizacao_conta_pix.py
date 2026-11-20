import time
from datetime import datetime
from pathlib import Path

from PIL import Image
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
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "11atualizacao_conta_pix"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    caminho_imagem = pasta_raiz / f"11atualizacao_conta_pix_{resultado}_{data_hora}.png"
    imagem_salva = navegador.save_screenshot(str(caminho_imagem))

    if imagem_salva:
        # Passo a imagem pelo Pillow e salvo a print.
        with Image.open(caminho_imagem) as imagem:
            imagem.convert("RGB").save(caminho_imagem, format="PNG")
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_ct11_atualizacao_conta_pix():
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

        # Guardo o saldo que aparece antes de fazer o PIX.
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

        # Faço um PIX de R$ 10,00 pra conta de destino do teste.
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

        navegador.find_element(By.ID, "pix-confirm").click()
        time.sleep(1)
        sucesso = WebDriverWait(navegador, 15).until(
            EC.visibility_of_element_located((By.ID, "pix-transfer-success"))
        )
        assert sucesso.is_displayed()
        assert "PIX REALIZADO" in sucesso.text

        # Volto pro início e confiro o saldo depois do PIX.
        navegador.find_element(By.ID, "pix-finish").click()
        time.sleep(1)
        saldo_esperado = round(saldo_inicial - 10.00, 2)
        WebDriverWait(navegador, 10).until(
            lambda driver: round(ler_saldo(driver), 2) == saldo_esperado
        )
        saldo_atualizado = ler_saldo(navegador)
        assert round(saldo_atualizado, 2) == saldo_esperado
        capturar_tela(navegador, "saldo_atualizado")

        # Confiro se o PIX aparece no começo do extrato.
        transacoes = WebDriverWait(navegador, 10).until(
            lambda driver: driver.find_elements(By.CSS_SELECTOR, "button.transaction")
        )
        assert len(transacoes) > 0, "O extrato não apresentou transações."
        transacao_mais_recente = transacoes[0]
        texto_transacao = transacao_mais_recente.text.replace("\xa0", " ")

        assert "PIX enviado" in texto_transacao
        assert f"Para {nome_destinatario}" in texto_transacao
        assert "R$" in texto_transacao and "10,00" in texto_transacao
        assert email_destinatario in texto_transacao or nome_destinatario in texto_transacao
        capturar_tela(navegador, "historico_pix")

    except Exception:
        capturar_tela(navegador, "falha")
        raise

    finally:
        print("\nO navegador será fechado em 5 segundos...")
        time.sleep(5)
        navegador.quit()


if __name__ == "__main__":
    test_ct11_atualizacao_conta_pix()
