import time
from datetime import datetime
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fixos import EMAIL_TESTE, SENHA_TESTE


def capturar_tela(navegador, resultado):
    # Aqui fica a pasta das prints desse teste.
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "3logout"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    caminho_imagem = pasta_raiz / f"3logout_{resultado}_{data_hora}.png"
    imagem_salva = navegador.save_screenshot(str(caminho_imagem))

    if imagem_salva:
        # Passo a imagem pelo Pillow e salvo a print.
        with Image.open(caminho_imagem) as imagem:
            imagem.convert("RGB").save(caminho_imagem, format="PNG")
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_ct03_logout():
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

        botao_sair = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.ID, "logout"))
        )
        token_antes = navegador.execute_script(
            "return window.localStorage.getItem('unipay-token');"
        )
        assert token_antes, "O token de sessão não foi criado após o login."

        # Clico em sair pra encerrar a sessão.
        botao_sair.click()
        time.sleep(1)

        campo_login = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "login-email"))
        )
        campo_senha = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "login-password"))
        )
        assert campo_login.is_displayed()
        assert campo_senha.is_displayed()

        token_depois = navegador.execute_script(
            "return window.localStorage.getItem('unipay-token');"
        )
        local_storage_len = navegador.execute_script("return window.localStorage.length;")
        assert token_depois is None, "O token permaneceu no localStorage após o logout."
        assert local_storage_len == 0, "O localStorage deveria estar vazio após o logout."

        # Tento abrir o início de novo sem estar logado.
        navegador.get("http://localhost:8080/")
        time.sleep(1)
        campo_login = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "login-email"))
        )
        assert campo_login.is_displayed()
        assert navegador.execute_script(
            "return window.localStorage.getItem('unipay-token');"
        ) is None

        capturar_tela(navegador, "sucesso")

    except Exception:
        capturar_tela(navegador, "falha")
        raise

    finally:
        print("\nO navegador será fechado em 5 segundos...")
        time.sleep(5)
        navegador.quit()


if __name__ == "__main__":
    test_ct03_logout()
