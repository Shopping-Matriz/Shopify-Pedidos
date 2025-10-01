"""Módulo de captura dos pedidos pagos da Shopify"""

import time
import schedule
from sqlalchemy import Case, Null, desc, false

from auxiliar import *
from representantes import *
from shopify_service import *
from alterdata_service import *


def integrar_pedidos():
    """Integra pedidos não processados e insere no ERP."""
    pedidos = pegar_pedidos_pagos(first=125)
    if not pedidos:
        print(f"{BOLD}{YELLOW}\n🟡 Sem pedidos para integrar {RESET}")
        print("\n\n⏳ Aguardando próximas execuções...\n")
        return
    print(f"{BOLD}{GREEN}\n 💬  Iniciando integração de pedidos... \n{RESET}")
    for pedido in pedidos:
        dados_pedido = pedido["node"]
        pedidos_importado = verifica_pedido_importado(dados_pedido["name"].lstrip("#"))
        cd_pedido_shopify = dados_pedido["name"]
        if pedidos_importado:
            print(
                f"{BOLD}{YELLOW}\n ! pedido [{cd_pedido_shopify}] já importado{RESET}"
            )
            continue
        transactions = dados_pedido.get("transactions", [])
        info_pagamento = next(
            (t for t in reversed(transactions) if t.get("status") == "SUCCESS"), None
        )
        gateway_pagamento = info_pagamento["gateway"] if info_pagamento else None
        info_envio = dados_pedido["shippingLine"]
        # ---------------------------//// Cliente ////----------------------------
        dados_cliente = dados_pedido["customer"]
        cliente_cpf_cnpj = dados_pedido["localizedFields"]["nodes"][0]["value"]
        cpf_cnpj_formatado = formatar_cpf_cnpj(cliente_cpf_cnpj)
        tp_cliente = verificar_tipo_cliente(cliente_cpf_cnpj)
        dados_endereco_entrega = dados_pedido["shippingAddress"]
        if not dados_endereco_entrega:
            dados_endereco_entrega = dados_pedido["billingAddress"]
        if tp_cliente == "F":
            nome_cliente = dados_cliente["displayName"].upper()
        elif tp_cliente == "J":
            nome_cliente = (dados_endereco_entrega.get("company") or "").upper() or (
                dados_cliente.get("displayName") or ""
            ).upper()
        else:
            nome_cliente = dados_cliente["displayName"].upper()
        if cpf_cnpj_formatado:
            id_pessoa = verifica_cliente(cpf_cnpj_formatado)
            if not id_pessoa:
                prox_cliente = pega_prox_ident_cod("Pessoa", "IdPessoa", "IdPessoa")
                cadastra_cliente(
                    prox_cliente[0],
                    prox_cliente[1],
                    nome_cliente,
                    cpf_cnpj_formatado,
                    tp_cliente,
                )
                id_pessoa = prox_cliente[0]
        else:
            print(f"{RED} ! Pedido [{cd_pedido_shopify}] sem cliente {RESET}")
            continue
        # ----------------//// Cep, Endereço ,Cidade, Estado, Bairro e contato ////------------------
        dados_cep = verifica_cep(dados_endereco_entrega["zip"])
        if not dados_cep:
            print(
                f"{BOLD}{YELLOW}\n ⚠  pedido [{cd_pedido_shopify}] com CEP não cadastrado no Bimer, usando ViaCep para validar dados{RESET}"
            )
        nm_logradouro_cep = dados_cep[2] if dados_cep else None
        if dados_cep:
            id_bairro = dados_cep[0] if dados_cep else None
            id_cidade = dados_cep[1] if dados_cep else None
            nm_logradouro = dados_cep[2] if dados_cep else None
            tp_logradouro = dados_cep[3] if dados_cep else None
        else:
            dados_cep = obter_dados_cep(
                re.sub(r"\D", "", dados_endereco_entrega["zip"])
            )
            if "erro" in dados_cep:
                print(
                    f"{BOLD}{RED}\n ❌ pedido [{cd_pedido_shopify}] não integrado, CEP inválido, ViaCep não conseguiu validar. Verifique Cep na Shopify{RESET}"
                )
                continue
            # --// cidade, estado //--
            id_cidade = verifica_cidade(
                dados_endereco_entrega["city"], dados_endereco_entrega["provinceCode"]
            )
            if not id_cidade:
                prox_cidade = pega_prox_ident_cod("Cidade", "IdCidade", "IdCidade")
                cadastra_cidade(
                    prox_cidade[0],
                    prox_cidade[1],
                    dados_endereco_entrega["city"].upper(),
                    dados_endereco_entrega["provinceCode"].upper(),
                )
                id_cidade = prox_cidade[0]
            # --// Bairro //--
            bairro = dados_cep.get("bairro", "")
            id_bairro = verifica_bairro(bairro.upper())
            if not id_bairro:
                prox_bairo = pega_prox_ident_cod("Bairro", "IdBairro", "IdBairro")
                cadastra_bairro(
                    prox_bairo[0], prox_bairo[1], dados_cep["bairro"].upper()
                )
                id_bairro = prox_bairo[0]
        # --// endereço e contato //--
        nr_logradouro = extrair_numero_endereco(dados_endereco_entrega["address1"])
        nm_logradouro = nm_logradouro_cep or extrair_nome_endereco(
            dados_endereco_entrega["address1"]
        )
        endereco_2 = dados_endereco_entrega.get("address2", "") or ""
        complemento = re.sub(r"^[^\wÀ-ÿ]+", "", endereco_2.split(",", 1)[0].strip())
        cd_endereco = verifica_endereco(
            id_pessoa, dados_endereco_entrega["zip"], nm_logradouro, nr_logradouro
        )
        id_contato = verifica_contato(id_pessoa, dados_cliente["displayName"].upper())
        contato_cadastrado = false
        if not cd_endereco:
            cd_endereco = pega_prox_coc_endereco(id_pessoa)
            if not nm_logradouro_cep:
                tp_logradouro = ""
            cadastra_endereco(
                id_pessoa,
                cd_endereco,
                id_pessoa,
                nm_logradouro.upper(),
                nr_logradouro,
                complemento,
                dados_endereco_entrega["zip"],
                id_bairro,
                cpf_cnpj_formatado,
                id_cidade,
                dados_endereco_entrega["provinceCode"],
                dados_cliente["displayName"].upper(),
                tp_logradouro,
            )
            id_pessoa_endereco_contato = pega_prox_ident(
                "PessoaEndereco_Contato",
                "IdPessoaEndereco_Contato",
                "IdPessoaEndereco_Contato",
            )
            cadastra_contato(
                id_pessoa_endereco_contato,
                id_pessoa,
                cd_endereco,
                dados_cliente["displayName"].upper(),
            )
            cadastra_tipo_contato(
                id_pessoa_endereco_contato,
                cd_endereco,
                id_pessoa,
                (dados_cliente.get("defaultEmailAddress") or {}).get("emailAddress", "")
                or "",
                (dados_endereco_entrega.get("phone") or "").replace("+55", "", 1)
                or (dados_cliente.get("defaultPhoneNumber") or {}).get(
                    "phoneNumber", ""
                )
                or "",
            )
            contato_cadastrado = true
        if contato_cadastrado == False and not id_contato:
            id_pessoa_endereco_contato = pega_prox_ident(
                "PessoaEndereco_Contato",
                "IdPessoaEndereco_Contato",
                "IdPessoaEndereco_Contato",
            )
            cadastra_contato(
                id_pessoa_endereco_contato,
                id_pessoa,
                cd_endereco,
                dados_cliente["displayName"].upper(),
            )
            cadastra_tipo_contato(
                id_pessoa_endereco_contato,
                cd_endereco if not cd_endereco else cd_endereco,
                id_pessoa,
                (dados_cliente.get("defaultEmailAddress") or {}).get("emailAddress", "")
                or "",
                (dados_endereco_entrega.get("phone") or "").replace("+55", "", 1)
                or (dados_cliente.get("defaultPhoneNumber") or {}).get(
                    "phoneNumber", ""
                )
                or "",
            )
        # else:
        #     atualiza_endereco(
        #         nm_logradouro.upper(),
        #         nr_logradouro,
        #         dados_endereco_entrega["address2"],
        #         dados_endereco_entrega["zip"],
        #         id_bairro,
        #         cpf_cnpj_formatado,
        #         id_cidade,
        #         dados_endereco_entrega["provinceCode"],
        #         dados_cliente["displayName"].upper(),
        #         id_pessoa,
        #         cd_endereco,
        #         nome_cliente,
        #         id_contato,
        #     )
        # --------------------/// Representante ///----------------
        tags = dados_pedido["tags"]
        id_representante = pegar_representante(tags)
        if id_representante == "00A000M4XT":
            id_unidade_negocio = 0
        else:
            id_unidade_negocio = 4
        # --------------------/// Pedido ///----------------
        if tp_cliente == "F":
            id_setor_endereco = "00A0000046"
            cd_empresa = "1000"
        else:
            id_setor_endereco = "00A00000E6"
            cd_empresa = "432"
        dt_emissao = converter_data_sql_server(dados_pedido["createdAt"])
        prox_pedido = pega_prox_ident_cod(
            "PedidoDeVenda", "IdPedidoDeVenda", "IdPedidoDeVenda"
        )
        # obs_cliente = (
        #     dados_pedido["note"]
        #     if dados_pedido["note"]
        #     else "Sem observações do Cliente"
        # )
        obs_pagamento = (
            f"{gateway_pagamento} {info_pagamento.get('paymentDetails', {}).get('company','')}({info_pagamento.get('paymentDetails', {}).get('number','')[-4:]})"
            if gateway_pagamento and "cartão" in gateway_pagamento.lower()
            else gateway_pagamento
        )
        titulo = info_envio.get("title", "Sem info")

        if titulo.lower() != "frete próprio":
            obs_retirada = f"retirada - {titulo}"
        else:
            obs_retirada = titulo
        obs_pedido = f"{obs_pagamento.upper()}\n{obs_retirada.upper()}"  # OBS CLIENTE: {obs_cliente.upper()}\n
        insere_pedido_venda(
            prox_pedido[0],
            prox_pedido[1],
            cd_empresa,
            id_pessoa,
            cd_endereco,
            dt_emissao,
            cd_pedido_shopify.lstrip("#"),
            id_setor_endereco,
            obs_pedido,
            dados_cliente["displayName"].upper()
            + " - "
            + (dados_endereco_entrega.get("phone") or "").replace("+55", "", 1),
            id_unidade_negocio,
        )
        # --------------------/// Itens ///----------------
        vl_total = float(
            dados_pedido.get("subtotalPriceSet", {})
            .get("shopMoney", {})
            .get("amount", 0)
        )
        itens = dados_pedido["lineItems"]["edges"]
        itens_filtrados = [
            item
            for item in itens
            if item["node"]["title"]
            not in ["Serviço de Montagem", "Taxa de deslocamento"]
        ]
        itens_montagen = [
            item
            for item in itens
            if item["node"]["title"] in ["Serviço de Montagem", "Taxa de deslocamento"]
        ]
        qtd_itens = len(itens_filtrados)
        vl_frete_total = float(
            dados_pedido.get("totalShippingPriceSet", {})
            .get("shopMoney", {})
            .get("amount", 0)
        )
        vl_desconto_total = float(
            dados_pedido.get("totalDiscountsSet", {})
            .get("presentmentMoney", {})
            .get("amount", 0)
        )
        if gateway_pagamento == "Pagar.me - PIX":
            vl_desconto_total = vl_desconto_total + 0.09 * vl_total
        vl_outros_total = (
            sum(
                float(
                    item["node"]["discountedUnitPriceSet"][
                        "presentmentMoney"
                    ]["amount"]
                )
                * float(item["node"]["quantity"])
                for item in itens_montagen
            )
            if itens_montagen
            else 0
        )
        vl_frete_parcial = vl_frete_total / qtd_itens if qtd_itens > 0 else 0
        vl_desconto_parcial = vl_desconto_total / qtd_itens if qtd_itens > 0 else 0
        vl_outros_parcial = float(vl_outros_total) / qtd_itens if qtd_itens > 0 else 0
        for item in itens_filtrados:
            dados_item = item["node"]
            kit = verifica_produto_kit(dados_item["sku"])
            variant_compare_at_price = float(
                dados_item["variant"]["compareAtPrice"] or 0
            )
            variant_price = float(dados_item["variant"]["price"] or 0)
            if (variant_compare_at_price - variant_price) > 0:
                desconto_item = variant_compare_at_price - variant_price
            else:
                desconto_item = 0
            if kit == True:
                itens_composicao = pega_composicao_produto(dados_item["sku"])
                qtd_itens_composicao = len(itens_composicao)
                vl_acrescimo_rateado = (
                    vl_frete_parcial / qtd_itens_composicao
                    if qtd_itens_composicao > 0
                    else 0
                )
                vl_desconto_rateado = (
                    (vl_desconto_parcial + desconto_item * item["node"]["quantity"])
                    / qtd_itens_composicao
                    if qtd_itens_composicao > 0
                    else 0
                )
                vl_despesas_rateado = (
                    vl_outros_parcial / qtd_itens_composicao
                    if qtd_itens_composicao > 0
                    else 0
                )
                for id_bimer, qtd, vl, peso_b, peso_l in itens_composicao:
                    prox_item = pega_prox_ident(
                        "PedidoDeVendaItem",
                        "IdPedidoDeVendaItem",
                        "IdPedidoDeVendaItem",
                    )
                    insere_pedido_venda_item(
                        prox_pedido[0],
                        prox_item,
                        id_bimer,
                        item["node"]["quantity"] * qtd,
                        vl,
                        vl * item["node"]["quantity"] * qtd,
                        vl_acrescimo_rateado,
                        vl_desconto_rateado,
                        vl_despesas_rateado,
                        id_setor_endereco,
                        "cfop",
                        peso_b,
                        peso_l,
                    )
                    cadastra_representante_pvi(prox_item, id_representante)
            else:
                prox_item = pega_prox_ident(
                    "PedidoDeVendaItem", "IdPedidoDeVendaItem", "IdPedidoDeVendaItem"
                )
                vl_acrescimo_rateado = vl_frete_parcial
                vl_desconto_rateado = (
                    vl_desconto_parcial + desconto_item * item["node"]["quantity"]
                )
                vl_despesas_rateado = vl_outros_parcial
                dados_produto = pega_dados_produto(item["node"]["sku"])
                insere_pedido_venda_item(
                    prox_pedido[0],
                    prox_item,
                    dados_produto[0],
                    item["node"]["quantity"],
                    dados_produto[3],
                    dados_produto[3] * item["node"]["quantity"],
                    vl_acrescimo_rateado,
                    vl_desconto_rateado,
                    vl_despesas_rateado,
                    id_setor_endereco,
                    "cfop",
                    dados_produto[1],
                    dados_produto[2],
                )
                cadastra_representante_pvi(prox_item, id_representante)
        # --------------------/// Pagamento ///----------------
        # add cod_pagamentpo_aux.txt se for adicionar pagamentos na integração
        if "cartão" in gateway_pagamento.lower():
            eh_cartão = 1
        else:
            eh_cartão = 0
        print(
            f"{BOLD}{GREEN} ✔  pedido [{cd_pedido_shopify}] integrado com sucesso\n{RESET}"
        )
        adicionar_tag_integrado(dados_pedido["id"], eh_cartão)
    print("\n\n⏳ Aguardando próximas execuções...")


# ______________________________/// Inicialização / Agendamento ///____________________________________

print("\n🔰 Sistema de integração iniciado ")
integrar_pedidos()
schedule.every(10).minutes.do(
    integrar_pedidos
)  # <-- Agendar a função para rodar a cada 10 minutos
while True:
    schedule.run_pending()
    time.sleep(1)
