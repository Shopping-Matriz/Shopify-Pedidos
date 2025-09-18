"""Módulo de Representantes"""

def pegar_representante(tags: list[str] | None) -> str:
    """
    Retorna o representante com base nas tags.
    Regras:
      - Se não tiver "Afiliado" → retorna "00A000M4XT"
      - Se tiver "Afiliado" → busca no mapeamento de nomes
      - Se não achar nenhum nome → retorna "00A000M4XT" (fallback)
    """
    mapa_representantes = {
        "Bruno Bittencourt": "00A000L2FI",
        "Stefany Figueiredo": "00A000ML7M",
        "Anne Betta": "00A000MDJ7",
        "Izabela Souza": "00A000MVIG",
        "Matheus Batista": "00A000MVKB",
        "Luana Pereira": "00A000MN6Q",
        "Liana Alves": "00A000MDP5",
        "Marcus Vollaro": "00A000007Q",
        "Jamilton Corrêa": "00A0000075",
        "Marli Marinho": "00A000007T",
        "Cristiane Almeida": "00A0003RQH",
        "Thacilla Pereira": "00A000MPSL",
        "Gabriela Xavier": "00A0004BLZ",
        "Cristina Gaspar": "00A0007JZ7",
        "Jandinete Marques": "00A000MDL6",
        "Mario Cruz": "00A0009D0K",
        "Jonathan William": "00A000MK4P",
        "Vanessa Caetano": "00A0005VM6",
        "Rosane Fernandes": "00A000MDL9",
        "Jeane Mary": "00A0000077",
        "Janice Brito": "00A000005Z",
        "Sheila Correia": "00A0008JFL",
        "Renato Damasceno": "00A0009U9M",
        "Elaine Gomes": "00A000MIC5",
        "Thiago Candido": "00A000241I",
        "Leonardo Moura": "00A000007E",
        "Dayane Lima": "00A000KYVQ",
        "Márcia Schueler": "00A00004XY",
        "Paulino Nascimento": "00A000A97T",
        "Alice Oliveira": "00A000MYZA",
    }

    if "Afiliado" not in tags:
        # print("00A000M4XT") #--Testar
        return "00A000M4XT"

    for nome, representante in mapa_representantes.items():
        if nome in tags:
            # print(representante) #--Testar
            return representante
    # print("00A000M4XT") #--Testar
    return "00A000M4XT"  # fallback


# # Exemplo de uso
# dados_pedido = {
#     "tags": [ "Afiliado","Anne Betta", "✔ Integrado", "💳 Verificar"]
# }

# representante = pegar_representante(dados_pedido.get("tags", []))
# print(f"Representante: {representante}")
