import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fixos import EMAIL_DESTINO, EMAIL_TESTE, NOME_DESTINO, SENHA_TESTE


def capturar_tela(navegador, resultado):
    # Aqui fica a pasta das prints desse teste.
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "8dados_destinatario_pix"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    # Pego a data e a hora pra não repetir o nome da print.
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    caminho_imagem = pasta_raiz / f"8dados_destinatario_pix_{resultado}_{data_hora}.png"

    # Tiro uma print pra mostrar o resultado.
    imagem_salva = navegador.save_screenshot(str(caminho_imagem))
    if imagem_salva:
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_ct08_consultar_destinatario_pix():
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

        # Abro o PIX e informo a chave cadastrada da conta de destino.
        navegador.find_element(By.ID, "make-pix").click()
        campo_chave = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "pix-recipient-key"))
        )
        campo_chave.send_keys(EMAIL_DESTINO)
        time.sleep(1)
        navegador.find_element(By.ID, "pix-next-key").click()
        time.sleep(1)

        # Confiro se o sistema encontrou a conta certa antes de informar o valor.
        campo_valor = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.ID, "pix-amount-input"))
        )
        nome_confirmacao = navegador.find_element(By.CSS_SELECTOR, ".recipient-pill strong").text
        chave_confirmacao = navegador.find_element(By.CSS_SELECTOR, ".recipient-pill small:last-child").text
        mensagens_erro = navegador.find_elements(By.CSS_SELECTOR, "[role='alert']")

        assert campo_valor.is_displayed()
        assert len(mensagens_erro) == 0
        assert nome_confirmacao == NOME_DESTINO
        assert chave_confirmacao == EMAIL_DESTINO

        # Salvo a print com os dados do destinatário encontrado.
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
    test_ct08_dados_destinatario_pix()
