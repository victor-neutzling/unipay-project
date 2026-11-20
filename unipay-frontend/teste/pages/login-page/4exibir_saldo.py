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


def converter_saldo(texto):
    texto = texto.replace("\xa0", " ").strip()
    correspondencia = re.fullmatch(r"R\$\s*([\d.]+,\d{2})", texto)
    assert correspondencia, f"Formato de saldo inesperado: {texto}"
    valor = correspondencia.group(1).replace(".", "").replace(",", ".")
    return float(valor)


def consultar_saldo_da_conta(navegador):
    # Pego o saldo pela API pra comparar com o que aparece na tela.
    resultado = navegador.execute_async_script("""
        const concluir = arguments[0];
        const token = localStorage.getItem("unipay-token");
        fetch("/api/account", {
          headers: { Authorization: `Bearer ${token}` }
        })
          .then(async (resposta) => ({
            ok: resposta.ok,
            dados: await resposta.json()
          }))
          .then(({ ok, dados }) => concluir({ ok, saldo: dados.user?.balance, erro: dados.error }))
          .catch((erro) => concluir({ ok: false, erro: String(erro) }));
    """)
    assert resultado["ok"], f"Não foi possível consultar a conta pela API: {resultado.get('erro')}"
    assert resultado["saldo"] is not None, "A API não retornou o saldo da conta."
    return float(resultado["saldo"])


def capturar_tela(navegador, resultado):
    # Aqui fica a pasta das prints desse teste.
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "4exibir_saldo"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    caminho_imagem = pasta_raiz / f"4exibir_saldo_{resultado}_{data_hora}.png"
    imagem_salva = navegador.save_screenshot(str(caminho_imagem))

    if imagem_salva:
        # Passo a imagem pelo Pillow e salvo a print.
        with Image.open(caminho_imagem) as imagem:
            imagem.convert("RGB").save(caminho_imagem, format="PNG")
        print(f"\nEvidência salva em: {caminho_imagem}")
    else:
        print("\nNão foi possível salvar a evidência.")


def test_ct04_exibir_saldo():
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

        # Espero o card aparecer e confiro o saldo.
        card_saldo = WebDriverWait(navegador, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "section.balance-card"))
        )
        elemento_saldo = navegador.find_element(By.ID, "available-balance")
        assert card_saldo.is_displayed()
        assert elemento_saldo.is_displayed()

        texto_saldo = elemento_saldo.text
        assert "R$" in texto_saldo
        assert not any(valor in texto_saldo for valor in ("None", "NaN", "undefined", "•••"))
        saldo_tela = converter_saldo(texto_saldo)

        saldo_banco = consultar_saldo_da_conta(navegador)
        assert round(saldo_tela, 2) == round(saldo_banco, 2)
        time.sleep(1)

        # Atualizo a página pra ver se o saldo continua salvo.
        navegador.refresh()
        time.sleep(1)
        card_saldo = WebDriverWait(navegador, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "section.balance-card"))
        )
        WebDriverWait(navegador, 15).until(
            lambda driver: driver.find_element(By.ID, "available-balance").text.strip().startswith("R$")
        )
        assert card_saldo.is_displayed()

        saldo_apos_refresh = converter_saldo(navegador.find_element(By.ID, "available-balance").text)
        saldo_banco_apos_refresh = consultar_saldo_da_conta(navegador)
        assert round(saldo_apos_refresh, 2) == round(saldo_banco_apos_refresh, 2)
        assert round(saldo_apos_refresh, 2) == round(saldo_tela, 2)

        capturar_tela(navegador, "sucesso")

    except Exception:
        capturar_tela(navegador, "falha")
        raise

    finally:
        print("\nO navegador será fechado em 5 segundos...")
        time.sleep(5)
        navegador.quit()


if __name__ == "__main__":
    test_ct04_exibir_saldo()
