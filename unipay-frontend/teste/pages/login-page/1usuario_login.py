import time
from datetime import datetime
from pathlib import Path
from PIL import Image


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fixos import EMAIL_TESTE, SENHA_TESTE

def capturar_tela(navegador, resultado):
    # Aqui fica a pasta das prints desse teste.
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "1usuario_login"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    # Pego a data e a hora pra não repetir o nome da print.
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Salvo a print nessa pasta.
    caminho_imagem = (
        pasta_raiz
        / f"1usuario_login_{resultado}_{data_hora}.png"
    )

    # Tiro uma print pra mostrar o resultado.
    imagem_salva = navegador.save_screenshot(
        str(caminho_imagem)
    )

    if imagem_salva:
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_login_com_sucesso():
    service = Service(log_output="chromedriver.log", service_args=["--verbose"])
    opcoes = webdriver.ChromeOptions()
    opcoes.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    navegador = webdriver.Chrome(service=service, options=opcoes)

    try:
        navegador.maximize_window()

        # Abro o UniPay.
        navegador.get("http://localhost:8080/")
        time.sleep(2)

        # Coloco o e-mail da conta de teste.
        campo_usuario = navegador.find_element(
            By.ID,

            "login-email"
        )
        campo_usuario.send_keys(EMAIL_TESTE)
        time.sleep(2)

        # Coloco a senha da conta de teste.
        campo_senha = navegador.find_element(
            By.ID,
            "login-password"
        )
        campo_senha.send_keys(SENHA_TESTE)
        time.sleep(2)

        # Clico pra entrar na conta.
        botao_login = navegador.find_element(
            By.ID,
            "login-submit"
        )
        botao_login.click()

        # Espero o menu aparecer depois do login.
        titulo_menu = WebDriverWait(
            navegador,
            10
        ).until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, "side-label")
            )
        )

        # Confiro se o resultado apareceu certo.
        assert titulo_menu.text == "MENU"

        # Salvo a print do resultado.
        capturar_tela(navegador, "sucesso")

    except Exception:
        # Se der erro, também salvo uma print.
        capturar_tela(navegador, "falha")

        # Deixo o pytest mostrar o erro.
        raise

    finally:
        # Fecho o navegador mesmo se o teste der erro.
        print("\nO navegador será fechado em 5 segundos...")
        time.sleep(5)

        navegador.quit()
