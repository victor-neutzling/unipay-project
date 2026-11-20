import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def gerar_cpf_teste():
    # Uso o horário pra gerar um CPF diferente em cada tentativa.
    cpf = [int(numero) for numero in str(int(datetime.now().timestamp() * 1000000))[-9:]]

    for peso_inicial in (10, 11):
        soma = sum(numero * (peso_inicial - indice) for indice, numero in enumerate(cpf))
        resto = soma % 11
        cpf.append(0 if resto < 2 else 11 - resto)

    return "".join(str(numero) for numero in cpf)


def capturar_tela(navegador, resultado):
    # Aqui fica a pasta das prints desse teste.
    pasta_raiz = Path(__file__).resolve().parents[2] / "screenshots" / "2register"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    # Pego a data e a hora pra não repetir o nome da print.
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Salvo a print nessa pasta.
    caminho_imagem = (
        pasta_raiz
        / f"2register_{resultado}_{data_hora}.png"
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

        # Abro a tela de cadastro.
        botao_register = navegador.find_element(
            By.ID,
            "go-register"
        )
        botao_register.click()
        time.sleep(2)

        # Coloco o nome da conta nova.
        campo_nome = navegador.find_element(
            By.ID,
            "register-name"
        )
        campo_nome.send_keys("nome_teste")
        time.sleep(2)

        # Coloco um e-mail diferente pra cadastrar.
        campo_email = navegador.find_element(
            By.ID,
            "register-email"
        )
        email_cadastro = f"cadastro{datetime.now().strftime('%Y%m%d%H%M%S')}@email.test"
        campo_email.send_keys(email_cadastro)
        time.sleep(2)

        # Gero um CPF válido pra essa conta.
        campo_cpf = navegador.find_element(
            By.ID,
            "register-cpf"
        )
        campo_cpf.send_keys(gerar_cpf_teste())
        time.sleep(2)

        # Coloco uma senha pra conta nova.
        campo_senha = navegador.find_element(
            By.ID,
            "register-password"
        )
        campo_senha.send_keys("senha_teste_123")
        time.sleep(2)

        # Clico pra fazer o cadastro.
        botao_cadastrar = navegador.find_element(
            By.ID,
            "register-submit"
        )
        botao_cadastrar.click()

        time.sleep(2)
        # Espero o cadastro terminar e voltar pro login.
        titulo_login = WebDriverWait(
            navegador,
            10
        ).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "h2")
            )
        )
        # Confiro se o resultado apareceu certo.
        assert titulo_login.text == "Que bom ter\nvocê por aqui."

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
