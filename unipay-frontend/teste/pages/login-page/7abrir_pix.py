import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fixos import EMAIL_TESTE, SENHA_TESTE


def capturar_tela(navegador, resultado):
    # Aqui fica a pasta das prints desse teste.
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "7abrir_pix"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    # Pego a data e a hora pra não repetir o nome da print.
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Tiro uma print pra mostrar o resultado.
    caminho_imagem = pasta_raiz / f"7abrir_pix_{resultado}_{data_hora}.png"
    imagem_salva = navegador.save_screenshot(str(caminho_imagem))

    if imagem_salva:
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_ct07_abrir_tela_pix():
    opcoes = webdriver.ChromeOptions()
    opcoes.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    navegador = webdriver.Chrome(options=opcoes)

    try:
        navegador.maximize_window()

        # Abro o UniPay.
        navegador.get("http://localhost:8080/")
        time.sleep(2)

        # Entro com a conta de teste.
        campo_usuario = navegador.find_element(By.ID, "login-email")
        campo_usuario.send_keys(EMAIL_TESTE)
        time.sleep(1)

        campo_senha = navegador.find_element(By.ID, "login-password")
        campo_senha.send_keys(SENHA_TESTE)
        time.sleep(1)

        botao_login = navegador.find_element(By.ID, "login-submit")
        botao_login.click()

        # Espero o menu aparecer depois do login.
        titulo_menu = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "side-label"))
        )
        assert titulo_menu.text == "MENU"
        time.sleep(2)

        # Clico no atalho pra abrir a área PIX.
        botao_pix = navegador.find_element(By.ID, "make-pix")
        botao_pix.click()
        time.sleep(2)

        # Confiro se abriu a tela pra colocar a chave PIX.
        campo_chave_pix = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "pix-recipient-key"))
        )
        texto_passo = navegador.find_element(By.CLASS_NAME, "step-label").text

        assert campo_chave_pix.is_displayed()
        assert "Chave PIX do destinatário" in navegador.find_element(
            By.CSS_SELECTOR, "label[for='pix-recipient-key']"
        ).text
        assert "PASSO 1 DE 2" in texto_passo

        # Salvo a print da tela PIX.
        capturar_tela(navegador, "sucesso")

    except Exception:
        # Se der erro, também salvo uma print.
        capturar_tela(navegador, "falha")
        raise

    finally:
        print("\nO navegador será fechado em 5 segundos...")
        time.sleep(5)
        navegador.quit()


if __name__ == "__main__":
    test_ct07_abrir_tela_pix()
