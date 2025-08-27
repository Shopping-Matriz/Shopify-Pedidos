"""Módulo de captura dos pedidos pagos da Shopify"""

import time
import schedule

from auxiliar import *
from shopify_service import *
from alterdata_service import *


def integrar_pedidos():
    """Integra pedidos não processados e insere no ERP."""
    pedidos = pegar_pedidos_pagos(first=125)
    if not pedidos:
        print(f"{BOLD}{YELLOW}\n🟡 Sem pedidos para integrar {RESET}")
        return
    for pedido in pedidos:
        dados_pedido = pedido["node"]
        pedidos_importado = verifica_pedido_importado(dados_pedido["name"])
        if pedidos_importado:
            nome_pedido = dados_pedido["name"]
            print(f"{BOLD}{YELLOW} - pedido [{nome_pedido}] já importado{RESET}")
            continue
        # ---------------------------//// Cliente ////----------------------------
        dados_cliente = dados_pedido["customer"]
        cliente_cpf_cnpj = dados_pedido["localizedFields"]["nodes"][0]["value"]
        cpf_cnpj_formatado = formatar_cpf_cnpj(cliente_cpf_cnpj)
        if cliente_cpf_cnpj:
            id_pessoa = verifica_cliente(cliente_cpf_cnpj)
            if not id_pessoa:
                prox_cliente = pega_prox_ident_cod("Pessoa", "IdPessoa", "IdPessoa")
                tp_cliente = verificar_tipo_cliente(cliente_cpf_cnpj)
                cadastra_cliente(
                    prox_cliente[0],
                    prox_cliente[1],
                    dados_cliente["displayName"].upper(),
                    cpf_cnpj_formatado,
                    tp_cliente,
                )
                id_pessoa = prox_cliente[0]
        else:
            cd_pedido_shopify = dados_pedido["name"]
            print(f"{RED} ❗ Pedido [{cd_pedido_shopify}] sem cliente {RESET}")
            continue
        # ----------------//// Cep, Endereço ,Cidade, Estado, Bairro e contato ////------------------
        dados_endereco_entrega = dados_pedido["shippingAddress"]
        # --// Cep //--
        dados_cep = verifica_cep(dados_endereco_entrega["zip"])
        if dados_cep:
            id_bairro = dados_cep[0]
            id_cidade = dados_cep[1]
            nm_logradouro = dados_cep[2]
        else:
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
            dados_cep = obter_dados_cep(
                re.sub(r"\D", "", dados_endereco_entrega["zip"])
            )
            id_bairro = verifica_bairro(dados_cep["bairro"].upper())
            if not id_bairro:
                prox_bairo = pega_prox_ident_cod("Bairro", "IdBairro", "IdBairro")
                cadastra_bairro(
                    prox_bairo[0], prox_bairo[1], dados_cep["bairro"].upper()
                )
                id_bairro = prox_bairo[0]
        # --// endereço e contato //--
        nr_logradouro = extrair_numero_endereco(dados_endereco_entrega["address1"])
        nm_logradouro = nm_logradouro or extrair_nome_endereco(
            dados_endereco_entrega["address1"]
        )
        # print(dados_endereco_entrega["address2"])
        # print(nr_logradouro)
        cd_endereco = verifica_endereco(
            id_pessoa,
            dados_endereco_entrega["zip"],
            nr_logradouro,
            dados_endereco_entrega.get("address2", {}) or "",
        )
        # break
        id_contato = verifica_contato(id_pessoa, dados_cliente["displayName"].upper())
        if not cd_endereco:
            prox_endereco = pega_prox_coc_endereco(id_pessoa)
            cadastra_endereco(
                id_pessoa,
                prox_endereco,
                id_pessoa,
                nm_logradouro.upper(),
                nr_logradouro,
                dados_endereco_entrega["address2"].upper(),
                dados_endereco_entrega["zip"],
                id_bairro,
                cpf_cnpj_formatado,
                id_cidade,
                dados_endereco_entrega["provinceCode"],
                dados_cliente["displayName"].upper(),
            )
            cd_endereco = prox_endereco
            prox_contato = pega_prox_ident(
                "PessoaEndereco_Contato",
                "IdPessoaEndereco_Contato",
                "IdPessoaEndereco_Contato",
            )
            id_contato = prox_contato
            cadastra_tipo_contato(
                id_contato,
                cd_endereco,
                id_pessoa,
                dados_cliente.get("defaultEmailAddress", {}).get("emailAddress", "")
                or "",
                dados_cliente.get("defaultPhoneNumber", {}).get("phoneNumber", "")
                or "",
            )
        else:
            atualiza_endereco(
                nm_logradouro.upper(),
                nr_logradouro,
                dados_endereco_entrega["address2"],
                dados_endereco_entrega["zip"],
                id_bairro,
                cpf_cnpj_formatado,
                id_cidade,
                dados_endereco_entrega["provinceCode"],
                dados_cliente["displayName"].upper(),
                id_pessoa,
                cd_endereco,
                dados_cliente["displayName"].upper(),
                id_contato,
            )
        # --------------------/// Pedido ///----------------
        if tp_cliente == "F":
            id_setor_endereco = "00A0000046"
            cd_empresa = "1000"
        else:
            id_setor_endereco = "00A00000BA"
            cd_empresa = "424"
        dt_emissao = converter_data_sql_server(dados_pedido["createdAt"])
        prox_pedido = pega_prox_ident_cod(
            "PedidoDeVenda", "IdPedidoDeVenda", "IdPedidoDeVenda"
        )
        insere_pedido_venda(
            prox_pedido[0],
            prox_pedido[1],
            cd_empresa,
            id_pessoa,
            cd_endereco,
            dt_emissao,
            cd_pedido_shopify,
            id_setor_endereco,
            dados_pedido["note"],
        )
        # --------------------/// Itens ///----------------
        itens = dados_pedido["lineItems"]["edges"]
        itens_filtrados = [
            item
            for item in itens
            if item["node"]["id"] != "gid://shopify/LineItem/14758265225298"
        ]

        itens_montagen = [
            item
            for item in itens
            if item["node"]["id"] == "gid://shopify/LineItem/14758265225298"
        ]

        qtd_itens = len(itens_filtrados)

        vl_frete_total = pedido["totalShippingPriceSet"]["shopmoney"]["amount"]
        vl_desconto_total = pedido["totalDiscountsSet"]["presentmentMoney"]["amount"]
        vl_outros_total = sum(
            float(
                item["node"]["discountedUnitPriceAfterAllDiscountsSet"][
                    "presentmentMoney"
                ]["amount"]
            )
            for item in itens_montagen
        )

        vl_frete_parcial = vl_frete_total / qtd_itens if qtd_itens > 0 else 0
        vl_desconto_parcial = vl_desconto_total / qtd_itens if qtd_itens > 0 else 0
        vl_outros_parcial = vl_outros_total / qtd_itens if qtd_itens > 0 else 0

        for item in itens:
            dados_item = item["node"]
            if dados_item["id"] == "gid://shopify/LineItem/14758265225298":
                continue
            kit = verifica_produto_kit(dados_item["sku"])
            if kit is True:
                itens_composicao = pega_composicao_produto(dados_item["sku"])
                qtd_itens_composicao = len(itens_composicao)
                vl_acrescimo_rateado = (
                    vl_frete_parcial / qtd_itens_composicao
                    if qtd_itens_composicao > 0
                    else 0
                )
                vl_desconto_rateado = (
                    vl_desconto_parcial / qtd_itens_composicao
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
                        prox_item[0],
                        id_bimer,
                        item["quantity"] * qtd,
                        vl,
                        vl * item["quantity"] * qtd,
                        vl_acrescimo_rateado,
                        vl_desconto_rateado,
                        vl_despesas_rateado,
                        id_setor_endereco,
                        "cfop",
                        peso_b,
                        peso_l,
                    )
            else:
                prox_item = pega_prox_ident(
                    "PedidoDeVendaItem", "IdPedidoDeVendaItem", "IdPedidoDeVendaItem"
                )
                vl_acrescimo_rateado = vl_frete_parcial
                vl_desconto_rateado = vl_desconto_parcial
                vl_despesas_rateado = vl_outros_parcial
                dados_produto = pega_dados_produto(item["node"]["sku"])
                insere_pedido_venda_item(
                    prox_pedido[0],
                    prox_item[0],
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
        adicionar_tag_integrado(dados_pedido["id"])


# Executa imediatamente
print("\n🔰 Sistema de integração iniciado ")
integrar_pedidos()

# Agendar a função para rodar a cada 10 minutos
schedule.every(10).minutes.do(integrar_pedidos)

print("\n⏳ Aguardando próximas execuções...")
while True:
    schedule.run_pending()
    time.sleep(1)
