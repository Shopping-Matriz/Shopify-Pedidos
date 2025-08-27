"""Módulo de captura dos pedidos pagos da Shopify"""

import json
from datetime import datetime
import requests
from config import SHOPIFY_API_URL, SHOPIFY_ACCESS_TOKEN

YELLOW = "\033[93m"  # Amarelo claro
GREEN = "\033[92m"  # Verde claro
RED = "\033[91m"  # Vermelho claro
BOLD = "\033[1m"  # Negrito
RESET = "\033[0m"  # Resetar para estilo padrão

# NOT tag:Integrado

def pegar_pedidos_pagos(first=125):
    """Busca pedidos não Pagos e ainda não Importados no Shopify usando GraphQL."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = """
query GetUnprocessedOrders($first: Int!) {
  orders(
		first: $first,
		sortKey: CREATED_AT,
		reverse: true,
		query: "financial_status:EXPIRED AND fulfillment_status:UNFULFILLED AND name:2117 "
	) {
		edges {
      node {
        id,
        name,
        totalPriceSet {
					shopMoney {
						amount
					}
				},
        subtotalPriceSet {
					shopMoney {
						amount
					},
				}
        totalTaxSet {
					shopMoney {
						amount
					}
				},
        totalShippingPriceSet {
					shopMoney {
						amount
					}
				},
        currencyCode,
        createdAt,
				totalDiscountsSet{
					presentmentMoney{
						amount
					}
				}
				displayFulfillmentStatus,
				displayFinancialStatus,
				tags,
				note,
				customer {
					id,
					displayName,
					defaultEmailAddress {
						emailAddress
					},
					defaultPhoneNumber {
						phoneNumber
					},
					locale,
					note
				},
				localizedFields (first:100) {
					nodes{
            countryCode,
            key,
						purpose,
						title,
						value
					}
				},
				billingAddressMatchesShippingAddress,
				billingAddress{
					address1,
					address2,
					city,
					zip,
					company,
					country,
					province,
					provinceCode,
					formattedArea
				},
				shippingAddress{
					address1,
					address2,
					city,
					zip,
					company,
					country,
					province,
					provinceCode,
					formattedArea
				},
        transactions (first:100) {
          amountSet {
						shopMoney {
							amount
						}
					},
          kind,
          status,
					createdAt,
					processedAt,
          gateway
					paymentDetails {
						... on CardPaymentDetails {
								company,
                paymentMethodName,
								expirationMonth,
						}
					}
				},
				lineItems(first: 100) {
          edges {
            node {
							id,
              				title,
							sku,
							quantity,
							vendor,
							discountedUnitPriceAfterAllDiscountsSet{
								presentmentMoney{
									amount,
									currencyCode
								}
							}
							discountedUnitPriceSet{
								presentmentMoney{
									amount,
									currencyCode
								}
							}
            }
					}
				}
			}
		}
  }
}
    """
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    variables = {"first": first}
    response = requests.post(
        SHOPIFY_API_URL,
        headers=headers,
        json={
            "query": query,
            "variables": variables,
        },
        timeout=10,
    )

    if response.status_code == 200:
        data = response.json()
        edges = data.get("data", {}).get("orders", {}).get("edges", [])
        pedido_info = [
            {"id": edge["node"]["id"], "name": edge["node"]["name"]}
            for edge in edges
            if "node" in edge and "id" in edge["node"] and "name" in edge["node"]
        ]
        print(
            f"{BOLD}{GREEN}\n🟢 Pegando pedidos não Integrados | [{current_time}] {RESET}"
        )
        print(f"\n {json.dumps(pedido_info, indent=2)}")
        # print(edges)
        return edges
    else:
        print(
            f"{BOLD}{RED}\n🔴 Erro ao executar GraphQL: {response.status_code} {RESET}"
        )
        print(response.text)
        return []


def adicionar_tag_integrado(order_gid):
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    }

    # Mutação GraphQL para adicionar a tag "Integrado"
    mutation = """
    mutation orderUpdate($input: OrderInput!) {
        orderUpdate(input: $input) {
            order {
                id
                tags
            }
            userErrors {
                field
                message
            }
        }
    }
    """

    # Você pode sobrescrever as tags aqui. Se quiser manter tags existentes,
    # é necessário buscá-las primeiro. Neste exemplo, só adiciona "Integrado".
    variables = {"input": {"id": order_gid, "tags": "Integrado"}}

    response = requests.post(
        SHOPIFY_API_URL,
        json={"query": mutation, "variables": variables},
        headers=headers,
    )
    if response.status_code != 200:
        print("Erro HTTP:", response.status_code, response.text)
        return None

    data = response.json()
    if data.get("errors") or data["data"]["orderUpdate"]["userErrors"]:
        print("Erro GraphQL:", data)
        return None

    return data["data"]["orderUpdate"]["order"]


# -- TESTES --
# pegar_pedidos_pagos()  # Para Testar pegar pedidos

# adicionar_tag_integrado('gid://shopify/Order/6061713064018') # Para Testar adicionar tag
