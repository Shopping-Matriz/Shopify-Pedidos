"""Módulo de Funções axiliares"""

from datetime import datetime
import re
import requests


def verificar_tipo_cliente(cpf_cnpj):
    """
    Verifica se o número é CPF ou CNPJ com base na contagem de caracteres.
    """
    # Remover pontuações (pontos, traços e barras)
    cpf_cnpj_limpo = re.sub(r"[^\d]", "", cpf_cnpj)

    # Contar caracteres
    if len(cpf_cnpj_limpo) == 11:
        return "F"  # Pessoa Física (CPF)
    elif len(cpf_cnpj_limpo) == 14:
        return "J"  # Pessoa Jurídica (CNPJ)
    else:
        return "Inválido"  # Caso o número não seja válido


def formatar_cpf_cnpj(numero):
    """
    Remove caracteres não numéricos e formata um CPF ou CNPJ.
    """
    # Remover todos os caracteres não numéricos
    numero_limpo = re.sub(r"[^\d]", "", numero)

    # Verificar o tamanho do número limpo para decidir se é CPF ou CNPJ
    if len(numero_limpo) == 11:  # CPF
        return f"{numero_limpo[:3]}.{numero_limpo[3:6]}.{numero_limpo[6:9]}-{numero_limpo[9:]}"
    elif len(numero_limpo) == 14:  # CNPJ
        return f"{numero_limpo[:2]}.{numero_limpo[2:5]}.{numero_limpo[5:8]}/{numero_limpo[8:12]}-{numero_limpo[12:]}"
    else:
        return "Número inválido"


def extrair_numero_endereco(endereco):
    """
    Extrai a primeira numeração do endereço.
    """
    # Usar regex para buscar a primeira sequência de dígitos no endereço
    match = re.search(r"\b\d+\b", endereco)
    if match:
        return match.group()  # Retorna o número encontrado
    else:
        return ""


def obter_dados_cep(cep):
    """
    Pega informação do cep atraves da api do https://viacep.com.br/
    """
    # URL base da API
    url = f"https://viacep.com.br/ws/{cep}/json/"

    try:
        # Fazer a requisição para a API
        response = requests.get(url, timeout=10)

        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Retornar os dados em formato JSON
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
    # Remove a primeira sequência de dígitos seguida por possíveis espaços ou vírgulas
    resultado = re.sub(r"\b\d+\b.*", "", endereco).strip()
    return resultado


def converter_data_sql_server(data_api: str) -> str:
    """
    Converte uma data no formato ISO 8601 para o formato SQL Server.
    """
    try:
        # Convertendo a string da API para um objeto datetime
        data_datetime = datetime.strptime(data_api, "%Y-%m-%dT%H:%M:%SZ")
        # Formatando para o padrão SQL Server
        return data_datetime.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        # Tratando possíveis erros de formato
        return f"Erro ao converter a data: {e}"
