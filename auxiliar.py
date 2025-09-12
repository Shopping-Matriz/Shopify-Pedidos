"""Módulo de Funções axiliares"""

from datetime import datetime
import re
import requests

from alterdata_service import verifica_cep


def verificar_tipo_cliente(cpf_cnpj):
    """
    Verifica se o número é CPF ou CNPJ com base na contagem de caracteres.
    """
    cpf_cnpj_limpo = re.sub(r"[^\d]", "", cpf_cnpj)
    if len(cpf_cnpj_limpo) == 11:
        # print("F")  # --Testar Pessoa Física (CPF)
        return "F"
    elif len(cpf_cnpj_limpo) == 14:
        # print("F")
        return "J"  # --Testar Pessoa Jurídica (CNPJ)
    else:
        return "Inválido"


def formatar_cpf_cnpj(numero):
    """
    Remove caracteres não numéricos e formata um CPF ou CNPJ.
    """
    numero_limpo = re.sub(r"[^\d]", "", numero)
    if len(numero_limpo) == 11:  # CPF
        # print(
        #     f"{numero_limpo[:3]}.{numero_limpo[3:6]}.{numero_limpo[6:9]}-{numero_limpo[9:]}"
        # )  # --Testar
        return f"{numero_limpo[:3]}.{numero_limpo[3:6]}.{numero_limpo[6:9]}-{numero_limpo[9:]}"
    elif len(numero_limpo) == 14:  # CNPJ
        # print(
        #     f"{numero_limpo[:2]}.{numero_limpo[2:5]}.{numero_limpo[5:8]}/{numero_limpo[8:12]}-{numero_limpo[12:]}"
        # )  # --Testar
        return f"{numero_limpo[:2]}.{numero_limpo[2:5]}.{numero_limpo[5:8]}/{numero_limpo[8:12]}-{numero_limpo[12:]}"
    else:
        return "Número inválido"


def extrair_numero_endereco(endereco):
    """
    Extrai a primeira numeração do endereço.
    """
    match = re.search(r"\b\d+\b", endereco)
    if match:
        # print(match.group()) #--Testar
        return match.group()
    else:
        return ""


def obter_dados_cep(cep):
    """
    Pega informação do cep atraves da api do https://viacep.com.br/
    """
    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # print(response.json()) #--Testar
            return response.json()
        else:
            print(f"Erro ao acessar API: Código {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro ao conectar à API: {e}")
        return None


def extrair_nome_endereco(endereco):
    """
    Extrai o nome do logradouro (endereço sem a numeração).

    Parâmetros:
        endereco (str): O endereço em formato de texto.

    Retorna:
        str: O endereço sem a primeira numeração encontrada.
    """
    endereco = re.sub(r"[\u200B-\u200F\u2060\uFEFF]", "", endereco)
    resultado = re.sub(r"[, ]*\d+.*", "", endereco).strip()
    # print(resultado.upper()) #--Testar
    return resultado.upper()


def converter_data_sql_server(data_api: str) -> str:
    """
    Converte uma data no formato ISO 8601 para o formato SQL Server.
    """
    try:
        data_datetime = datetime.strptime(data_api, "%Y-%m-%dT%H:%M:%SZ")
        return data_datetime.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return f"Erro ao converter a data: {e}"


# -- TESTES --

# formatar_cpf_cnpj('053.987.427-28') #-- CPF

# formatar_cpf_cnpj('') #-- CNPJ

# verificar_tipo_cliente('053.987.427-28')

# obter_dados_cep('21941599')

# extrair_numero_endereco('Rua Oito de Dezembro, ⁠238')

# extrair_nome_endereco('Rua Oito de Dezembro, ⁠238')