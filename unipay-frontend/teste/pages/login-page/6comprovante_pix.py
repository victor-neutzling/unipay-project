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
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "6comprovante_pix"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    # Pego a data e a hora pra não repetir o nome da print.
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    caminho_imagem = pasta_raiz / f"6comprovante_pix_{resultado}_{data_hora}.png"

    # Tiro uma print pra mostrar o resultado.
    imagem_salva = navegador.save_screenshot(str(caminho_imagem))
    if imagem_salva:
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_ct06_exibir_comprovante_pix():
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

        # Entro com a conta de teste que tem PIX no extrato.
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

        # Procuro um PIX enviado e clico nele pra abrir o comprovante.
        transacao_pix = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class, 'transaction') and contains(., 'PIX enviado')]")
            )
        )
        transacao_pix.click()
        time.sleep(2)

        # Confiro os dados que aparecem no comprovante.
        drawer = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "transaction-drawer"))
        )
        data_transferencia = navegador.find_element(By.ID, "receipt-date").text
        nome_destinatario = navegador.find_element(By.ID, "receipt-recipient").text
        cpf_destinatario = navegador.find_element(By.ID, "receipt-cpf").text
        valor_transferido = navegador.find_element(By.ID, "receipt-amount").text

        assert drawer.is_displayed()
        assert data_transferencia != ""
        assert nome_destinatario != ""

        cpf_sem_pontos = cpf_destinatario.replace(".", "").replace("-", "")
        assert len(cpf_sem_pontos) == 11
        assert cpf_sem_pontos.isdigit()

        assert "R$" in valor_transferido
        assert any(caractere.isdigit() for caractere in valor_transferido)

        capturar_tela(navegador, "sucesso")
    except Exception:
        capturar_tela(navegador, "falha")
        raise
    finally:
        print("\nO navegador será fechado em 5 segundos...")
        time.sleep(5)
        navegador.quit()


if __name__ == "__main__":
    test_ct06_exibir_comprovante_pix()
