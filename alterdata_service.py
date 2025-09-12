"""Módulo cominicação com o BD (Altredata)"""

import pyodbc
from sqlalchemy import true
from config import DB_CONFIG


# ---- Conexão com banco de dados ----
def get_db_connection():
    """Cria uma conexão com o banco de dados."""
    conn = pyodbc.connect(
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
    )
    return conn


# \\\\\\\\\\\\\\\\\\\\\\\\\\\ ------ PEGAR PROXIMO IDENT.|COD. ----- \\\\\\\\\\\\\\\\\\\\\\\\\\\\


def pega_prox_ident(nm_tabela, nm_identificador_1, nm_identificador_2):
    """Pega somente o Próximo Identificador (Id) das tabelas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DECLARE @Id CHAR(10), @CdChamada VARCHAR(20)
            EXEC sp_GetCodeCompost
                ?, 
                ?, 
                ?, 
                NULL, 
                'S', 
                'N', 
                @Id output, 
                NULL

            SELECT 
                @Id as Identificador
            """,
            (nm_tabela, nm_identificador_1, nm_identificador_2),
        )
        row = cursor.fetchone()
        # print(row)  # -- Testar
        return row[0] if row else None
    finally:
        conn.close()


def pega_prox_ident_cod(nm_tabela, nm_identificador_1, nm_identificador_2):
    """Pega o Próximo Identificador (Id) e Código (CdChamda) das tabelas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DECLARE @Id CHAR(10), @CdChamada VARCHAR(20)
            EXEC sp_GetCodeCompost
                ?, 
                ?, 
                ?, 
                NULL, 
                'S', 
                'S', 
                @Id output, 
                @CdChamada output

            SELECT 
                RTRIM(LTRIM(@Id)) as Identificador, 
                RTRIM(LTRIM(@CdChamada)) as Codigo
            """,
            (nm_tabela, nm_identificador_1, nm_identificador_2),
        )
        row = cursor.fetchone()
        # print(row)  # -- Testar
        return row if row else None
    finally:
        conn.close()


def pega_prox_coc_endereco(id_pessoa):
    """Pega o Próximo código de endereço da tabela PessoaEndereco"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 
                coalesce(right(replicate('0', 2) + convert(VARCHAR,
                max(cdendereco)+1), 2), '01')
            FROM 
                PessoaEndereco (NoLock) WHERE RTRIM(LTRIM(IdPessoa)) = ?
            """,
            (id_pessoa),
        )
        row = cursor.fetchone()
        # print(row[0])  # -- Testar
        return row[0] if row else None
    finally:
        conn.close()


# TESTES --

# pega_prox_ident("Pessoa","IdPessoa","IdPessoa")  # Testar pega prox ident. e cod.

# pega_prox_ident_cod("Pessoa","IdPessoa","IdPessoa")  # Testar pega prox ident. e cod.

# pega_prox_coc_endereco("00A000N1GL")  # Testar pega prox código endereço.

# pega_prox_ident("PedidoDeVendaItem","IdPedidoDeVendaItem","IdPedidoDeVendaItem")  # Testar pega prox ident de item


# \\\\\\\\\\\\\\\\\\\\\\\\\\\ ------------- VERIFICAÇÕES ------------ \\\\\\\\\\\\\\\\\\\\\\\\\\\\


def verifica_cliente(cpf_cnpj):
    """Verifica se o cliente já existe no banco. Retorna dados do cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT TOP 1 P.IdPessoa as Identificador, P.CdChamada as Codigo, P.NmPessoa as Nome, P.CdCPF_CGC as CpfCnpj, 
            CASE WHEN IsNull(P.TpPessoa, 'J') = 'F' THEN 0 ELSE 1 END as Tipo, ISNULL(PETC.DsContato,'Sem info') 
            FROM Pessoa P (NoLock)
            LEFT OUTER JOIN PessoaEndereco PE (NoLock) ON (P.IdPessoa = PE.IdPessoa) AND (IsNull(PE.StEnderecoPrincipal, 'N') = 'S')
            LEFT OUTER JOIN PessoaEndereco_Contato PEC (NoLock) ON (PE.IdPessoa = PEC.IdPessoa) AND (PE.CdEndereco = PEC.CdEndereco) AND (IsNull(PEC.StContatoPrincipal, 'N') = 'S')
            LEFT OUTER JOIN PessoaEndereco_TipoContato PETC (NoLock) ON (PEC.IdPessoaEndereco_Contato = PETC.IdPessoaEndereco_Contato) AND (PETC.IdTipoContato = '0000000004')
            WHERE REPLACE(REPLACE(REPLACE(P.CdCPF_CGC,'.',''),'-',''),'/','') = REPLACE(REPLACE(REPLACE(?,'.',''),'-',''),'/','') AND NmCurto IS NOT NULL
            ORDER BY P.IdPessoa
            """,
            (cpf_cnpj),
        )
        row = cursor.fetchone()
        # print(f"{row}" if row else "Cliente não encontrado.")  # -- Testar
        return row[0] if row else None
    finally:
        conn.close()


def verifica_bairro(bairro):
    """Verifica se o Bairro já existe no banco. Retorna IdBairro"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT IdBairro FROM Bairro (NoLock) WHERE NMBAIRRO = ?;
            """,
            (bairro),
        )
        row = cursor.fetchone()
        # print(f"{row[0]}" if row else "Bairro não encontrado.")  # -- Testar
        return row[0] if row else None
    finally:
        conn.close()


def verifica_cidade(cidade, uf):
    """Verifica se o cidade já existe no banco. Retorna IdCidade"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT IdCidade FROM Cidade (NoLock) WHERE NMCIDADE = ? and IDUF = ?;
            """,
            (cidade, uf),
        )
        row = cursor.fetchone()
        # print(f"{row[0]}" if row else "Cidade não encontrada.")  # -- Testar
        return row[0] if row else None
    finally:
        conn.close()


def verifica_endereco(id_pessoa, cd_cep, nm_logradouro, nr_logradouro):
    """Verifica se o endereço já existe no banco. Retorna CdEndereco"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 
                CdEndereco Codigo
            FROM 
                PessoaEndereco (NoLock) 
            WHERE 
                RTRIM(LTRIM(IdPessoa)) = ? and 
                RTRIM(LTRIM(CdCEP)) = ? and 
                RTRIM(LTRIM(NmLogradouro)) = ? and
                RTRIM(LTRIM(NrLogradouro)) = ?
            """,
            (id_pessoa, cd_cep, nm_logradouro, nr_logradouro),
        )
        row = cursor.fetchone()
        # print(f"{row[0]}" if row else "Endereço não encontrado.")  # -- Testar
        return row[0] if row else None
    finally:
        conn.close()


def verifica_cep(cep):
    """Verifica se o cep já existe no banco. Retorna id_bairro e id_cidade"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                IdBairro,
                IdCidade,         
                NmLogradouro,
                TpLogradouro
            FROM
                CEP
            WHERE 
                CdCEP = ?
            """,
            (cep),
        )
        row = cursor.fetchone()
        # print(f"{row}" if row else "Cep não encontrado.")  # -- Testar
        return row if row else None
    finally:
        conn.close()


def verifica_contato(id_pessoa, contato):
    """Verifica se o contato já existe no banco. retorna IdContato"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 
                IdPessoaEndereco_Contato 
            FROM 
                PessoaEndereco_Contato (NoLock) 
            WHERE 
                (IdPessoa = ?) and 
                (DsContato = RTRIM(LTRIM(SUBSTRING(?, 1, 50))));
            """,
            (id_pessoa, contato),
        )
        row = cursor.fetchone()
        # print(f"{row[0]}" if row else "Contato não encontrado.")  # -- Testar
        return row[0] if row else None
    finally:
        conn.close()


def verifica_pedido_importado(cd_pedido):
    """Verifica se o pedido já foi importado. retorna 1 ou nome"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT TOP 1
                1
            FROM
                PedidoDeVenda PV (NoLock)
            WHERE
                PV.CdPedidoDeCompraCliente = ?
            """,
            (cd_pedido,),
        )
        row = cursor.fetchone()
        # print(f"{row[0]}" if row else "Pedido não encontrado.")  # -- Testar
        return row[0] if row else None
    finally:
        conn.close()


def verifica_produto_kit(cd_produto):
    """Verifica se o pruduto tem partes ou não"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 
                CASE 
                    WHEN COUNT(*) > 0 THEN 1 
                    ELSE 0 
                END AS TemComposicao
            FROM 
                Produto_Composicao PC
            INNER JOIN 
                CodigoProduto CP ON CP.IdProduto = PC.IdProduto AND CP.StCodigoPrincipal = 'S'
            INNER JOIN 
                Produto P ON P.IdProduto = CP.IdProduto
            WHERE 
                CP.CdChamada = ? AND P.TpProduto NOT IN ('N');
            """,
            (cd_produto),
        )
        row = cursor.fetchone()
        # print(f"{row[0]}" if row else "Produto sem partes")  # -- Testar
        return row[0] if row else None
    finally:
        conn.close()


# TESTES --

# verifica_cep("20550-201")  # Testar verifica cep

# verifica_cliente("053.987.427-28")  # Testar verifica cliente

# verifica_bairro("VILA ISABEL")  # Testar verifica bairro

# verifica_cidade("Rio de Janeiro", "RJ")  # Testar verifica cidade

# verifica_endereco("00A000MJ8D", "21610-320", "127", "")  # Testar verifica endereço

# verifica_contato("00A000MJ8D", "Hugo Bourguignon Rangel")  # Testar verifica endereço

# verifica_produto_kit('720050') #Testas verifica se tem kit

# \\\\\\\\\\\\\\\\\\\\\\\\\\\ ------------- INSERÇÕES ------------ \\\\\\\\\\\\\\\\\\\\\\\\\\\\


def cadastra_cliente(id_pessoa, cd_pessoa, nm_pessoa, cpf_cnpj, tp_pessoa):
    """Cadastra um novo cliente no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Pessoa
            (IdPessoa,CdChamada,NmPessoa,CdCPF_CGC,TpPessoa)
            VALUES
            (?,?,?,?,?)
            """,
            (id_pessoa, cd_pessoa, nm_pessoa, cpf_cnpj, tp_pessoa),
        )

        cursor.execute(
            """
            INSERT INTO PessoaComplementar
            (IdPessoa)
            VALUES
            (?)
            """,
            (id_pessoa),
        )

        cursor.execute(
            """
            INSERT INTO Cliente
            (IdPessoaCliente)
            VALUES
            (?)
            """,
            (id_pessoa),
        )
        conn.commit()
        return 1
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar cliente: {e}")
        return 0
    finally:
        conn.close()


def cadastra_bairro(id_bairro, cd_bairro, nm_bairro):
    """Cadastra uma novo bairro no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Bairro 
            (IDBAIRRO, CDCHAMADA, NMBAIRRO) 
            VALUES 
            (?, ?, ?)
            """,
            (id_bairro, cd_bairro, nm_bairro),
        )
        conn.commit()
        return 1
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar cidade: {e}")
        return 0
    finally:
        conn.close()


def cadastra_cidade(id_cidade, cd_cidade, nm_cidade, uf):
    """Cadastra uma nova cidade no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Cidade 
            (IDCIDADE, CDCHAMADA, NMCIDADE, IDUF) 
            VALUES (?, ?, ?, ?)
            """,
            (id_cidade, cd_cidade, nm_cidade, uf),
        )
        conn.commit()
        return 1
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar cidade: {e}")
        return 0
    finally:
        conn.close()


def cadastra_endereco(
    id_pessoa,
    cd_endereco,
    id_pessoa2,
    nm_logradouro,
    nr_logardouro,
    ds_complemento,
    cep,
    id_bairro,
    cpf_cnpj,
    id_cidade,
    uf,
    nm_pessoa,
):
    """Cadastra um novo endereço no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO PessoaEndereco
            (
                IdPessoa,
                CdEndereco,
                StEnderecoEntrega,
                StEnderecoPrincipal,
                StEnderecoCobranca,
                StEnderecoResidencial,
                StEnderecoComercial,
                StEnderecoCorrespondencia,
                NmLogradouro,
                NrLogradouro,
                DsComplemento,
                CdCEP,
                IdBairro,
                CdCPF_CGC,
                IdCidade,
                IdUF,
                NmPessoa,
                StAtivo,
                IdPais,
                TpContribuicaoICMS
            )
            VALUES
            (
                ?,
                RTRIM(LTRIM(SUBSTRING(?, 1, 2))),
                'S',
                CASE (SELECT COUNT(CdEndereco) FROM PessoaEndereco WHERE IdPessoa = ? AND StEnderecoPrincipal = 'S') WHEN 0 THEN 'S' ELSE 'N' END,
                'S',
                'S',
                'S',
                'S',
                UPPER(RTRIM(LTRIM(SUBSTRING(?, 1, 50)))),
                RTRIM(LTRIM(SUBSTRING(?, 1, 10))),
                UPPER(RTRIM(LTRIM(SUBSTRING(?, 1, 50)))),
                RTRIM(LTRIM(SUBSTRING(?, 1, 9))),
                ?,
                RTRIM(LTRIM(SUBSTRING(?, 1, 18))),
                ?,
                ?,
                RTRIM(LTRIM(SUBSTRING(?, 1, 50))),
                'S',
                '076',
                9
            )
            """,
            (
                id_pessoa,
                cd_endereco,
                id_pessoa2,
                nm_logradouro,
                nr_logardouro,
                ds_complemento,
                cep,
                id_bairro,
                cpf_cnpj,
                id_cidade,
                uf,
                nm_pessoa,
            ),
        )
        conn.commit()
        return 1
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar contato: {e}")
        return 0
    finally:
        conn.close()


def cadastra_contato(id_contato, id_pessoa, cd_endereco, nm_pessoa):
    """Cadastra um novo contato no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO PessoaEndereco_Contato
            (IdPessoaEndereco_Contato,IdPessoa,CdEndereco,DsContato,StContatoPrincipal)
            VALUES
            (?,?,RTRIM(LTRIM(SUBSTRING(?, 1, 2))),RTRIM(LTRIM(SUBSTRING(?, 1, 50))),'S')
            """,
            (id_contato, id_pessoa, cd_endereco, nm_pessoa),
        )
        conn.commit()
        return 1
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar contato: {e}")
        return 0
    finally:
        conn.close()


def cadastra_tipo_contato(id_contato, cd_endereco, id_pessoa, email, telefone):
    """Cadastra um novo contato no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO PessoaEndereco_TipoContato
                (
                    IdPessoaEndereco_Contato,
                    IdTipoContato,
                    CdEndereco,
                    IdPessoa,
                    DsContato
                )
                VALUES
                (
                    ?,
                    '0000000007',
                    ?,
                    ?,
                    ?
                )
            """,
            (id_contato, cd_endereco, id_pessoa, email),
        )

        cursor.execute(
            """
            INSERT INTO PessoaEndereco_TipoContato
                (
                    IdPessoaEndereco_Contato,
                    IdTipoContato,
                    CdEndereco,
                    IdPessoa,
                    DsContato
                )
                VALUES
                (
                    ?,
                    '0000000008',
                    ?,
                    ?,
                    ?
                )
            """,
            (id_contato, cd_endereco, id_pessoa, email),
        )

        cursor.execute(
            """
            INSERT INTO PessoaEndereco_TipoContato
                (
                    IdPessoaEndereco_Contato,
                    IdTipoContato,
                    CdEndereco,
                    IdPessoa,
                    DsContato
                )
                VALUES
                (
                    ?,
                    '0000000009',
                    ?,
                    ?,
                    ?
                )
            """,
            (id_contato, cd_endereco, id_pessoa, email),
        )

        cursor.execute(
            """
            INSERT INTO PessoaEndereco_TipoContato
                (
                    IdPessoaEndereco_Contato,
                    IdTipoContato,
                    CdEndereco,
                    IdPessoa,
                    DsContato
                )
                VALUES
                (
                    ?,
                    '0000000004',
                    ?,
                    ?,
                    ?
                )
            """,
            (id_contato, cd_endereco, id_pessoa, email),
        )

        cursor.execute(
            """
            INSERT INTO PessoaEndereco_TipoContato
                (
                    IdPessoaEndereco_Contato,
                    IdTipoContato,
                    CdEndereco,
                    IdPessoa,
                    DsContato
                )
                VALUES
                (
                    ?,
                    '0000000012',
                    ?,
                    ?,
                    ?
                )
            """,
            (id_contato, cd_endereco, id_pessoa, email),
        )

        cursor.execute(
            """
            INSERT INTO PessoaEndereco_TipoContato
                (
                    IdPessoaEndereco_Contato,
                    IdTipoContato,
                    CdEndereco,
                    IdPessoa,
                    DsContato
                )
                VALUES
                (
                    ?,
                    '0000000001',
                    ?,
                    ?,
                    REPLACE(?, '+55', '')
                )
            """,
            (id_contato, cd_endereco, id_pessoa, telefone),
        )
        conn.commit()
        return 1
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar tipos contatos: {e}")
        return 0
    finally:
        conn.close()


def insere_pedido_venda(
    id_pedido,
    cd_pedido,
    cd_empresa,
    id_pessoa,
    cd_endereco,
    dt_emissao,
    cd_pedido_shopify,
    id_setor_endereco,
    obs_pedido,
    obs_documento
):
    """Insere o novo pedido de venda"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO PedidoDeVenda
            (
                IdPedidoDeVenda,
                CdChamada,
                CdEmpresa,
                CdEmpresaEstoque,
                CdEmpresaFinanceiro,
                IdPessoaCliente,
                IdPessoaEntrega,
                CdEnderecoPrincipal,
                CdEnderecoCobranca,
                CdEnderecoEntrega,
                IdOperacao,
                IdOperacaoOE,
                DtEmissao,
                DtEntrada,
                DtEntrega,
                CdPedidoDeCompraCliente,
                IdSetor,
                StPedidoDeVenda,
                IdPreco,
                DsObservacaoPedido,
                IdMeioContato,
                IdUsuario,
                TpFretePorConta,
                DsEspecie,
                StFaturamentoParcial,
                IdMensagem1,
                TpAcrescimo,
                TpDesconto,
                StFaturadoTerceiros,
                DtReferenciaPagamento,
                IdSistema,
                TpIndAtendimentoPresencial,
                DsObservacaoDocumento,
                TpIndicativoIntermediador
            )
            VALUES
            (
                ?,
                ?,
                '97',
                ?,
                '97',
                ?,
                ?,
                ?,
                ?,
                ?,
                '00A000007V',
                '00A00000N6',
                Getdate(),
                ?, 
                DATEADD(HOUR, 14, CAST(CAST(DATEADD(DAY, 5, GETDATE()) AS DATE) AS DATETIME)),
                ?,
                ?,
                'A', 
                '00A0000002',
                ?,
                '00A000053Z',
                '00A0000001',
                'D',
                'VOLUME',
                'S',
                '00A000000B',
                'V',
                'V',
                'N',
                CONVERT(varchar(10), GETDATE(), 120),
                '0000000023',
                2,
                ?,
                0
            )
            """,
            (
                id_pedido,
                cd_pedido,
                cd_empresa,
                id_pessoa,
                id_pessoa,
                cd_endereco,
                cd_endereco,
                cd_endereco,
                dt_emissao,
                cd_pedido_shopify,
                id_setor_endereco,
                obs_pedido,
                obs_documento
            ),
        )

        cursor.execute(
            """
            INSERT INTO PedidoDeVendaHistorico
            (
                IdPedidoDeVenda
                ,DtHistorico
                ,TpPedidoDeVenda
                ,DsHistorico
            )
            VALUES
            (
                ?,
                GETDATE()
                ,'P'
                ,'Importação de pedido do site (Shopify)'
            )
            """,
            (id_pedido),
        )

        conn.commit()
        return 1
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar Pedido de Venda: {e}")
        return 0
    finally:
        conn.close()


def insere_pedido_venda_item(
    id_pedido_venda,
    id_pedido_venda_item,
    id_produto_bimer,
    qtd_pedida,
    vl_unitario,
    vl_item,
    vl_acrescimo,
    vl_descontos,
    vl_despesas,
    id_setor_endereco,
    cfop,
    vl_peso_bruto,
    vl_peso_liquido,
):
    """Insere um novo pedido de venda item"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO PedidoDeVendaItem (
                IdPedidoDeVenda,
                IdPedidoDeVendaItem,
                IdProduto,
                QtPedida,
                VlUnitario,
                VlItem,
                VlAcrescimoRateado, 
                VlDescontoRateado,
                VlOutrasDespesasRateado,
                StPedidodeVendaItem,
                DtEntrega,
                IdSetorSaida,
                IdCfop,
                TpAcrescimoItem,
                TpDescontoItem,
                StVendaMostruario,
                VlPesoBruto,
                VlPesoLiquido,
                TpOrigemProduto,
                CdSituacaoTributaria,
                StMercadoriaEntregue,
                TpEntrega,
                CdSituacaoTributariaCOFINS,
                CdSituacaoTributariaPIS,
                StEstoqueSetorSaida,
                StEstoqueSetorEntradaTransEmp
            )
            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?, 
                ?,
                ?,
                'A',
                DATEADD(HOUR, 14, CAST(CAST(DATEADD(DAY, 5, GETDATE()) AS DATE) AS DATETIME)),
                ?,
                ?,
                'V',
                'V',
                'N',
                ?,
                ?,
                0,
                '00',
                'N',
                'F',
                '01',
                '01',
                'S',
                'N'
            )
            """,
            (
                id_pedido_venda,
                id_pedido_venda_item,
                id_produto_bimer,
                qtd_pedida,
                vl_unitario,
                vl_item,
                vl_acrescimo,
                vl_descontos,
                vl_despesas,
                id_setor_endereco,
                cfop,
                vl_peso_bruto,
                vl_peso_liquido,
            ),
        )

        conn.commit()
        return 1
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar Pedido de Venda Item: {e}")
        return 0
    finally:
        conn.close()


# \\\\\\\\\\\\\\\\\\\\\\\\\\\ ------------- PEGAR DADOS ------------ \\\\\\\\\\\\\\\\\\\\\\\\\\\\


def pega_composicao_produto(sku):
    """Pega as composições de um produto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 
                pc.IdProdutoIntegrante,
                pc.QtProdutoIntegrante,
                pep.VlPreco,
                P.VlPesoBruto,
                P.VlPesoLiquido
            FROM 
                ShopifyIntegration.Product_Variants SPV
                INNER JOIN 
                    Produto_Composicao pc ON pc.IdProduto = SPV.Bimer_ProductId 
                INNER JOIN 
                    vw_ProdutoEmpresaPreco pep ON pep.IdProduto = pc.IdProdutoIntegrante AND pep.CdEmpresa = '1000' AND CdPreco = '01'
                INNER JOIN 
                    Produto P ON P.IdProduto = SPV.Bimer_ProductId
            WHERE
                SPV.Sku = ?
            """,
            (sku),
        )
        row = cursor.fetchall()
        # print(row)  # -- Testar
        return row if row else None
    finally:
        conn.close()


def pega_dados_produto(sku):
    """Pega dados do produto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                Bimer_ProductId,
                P.VlPesoBruto,
                P.VlPesoLiquido,
                SPV.Price
            FROM
                ShopifyIntegration.Product_Variants SPV
                INNER JOIN Produto P ON P.IdProduto = SPV.Bimer_ProductId
            WHERE
                SPV.Sku = ?
            """,
            (sku),
        )
        row = cursor.fetchone()
        # print(row)  # -- Testar
        return row if row else None
    finally:
        conn.close()


# pega_dados_produto('830144') #Testa dados do produto

# pega_composicao_produto('720050') #Testa compisições do produto

# \\\\\\\\\\\\\\\\\\\\\\\\\\\ ------------- ATUALIZAÇÔES ------------ \\\\\\\\\\\\\\\\\\\\\\\\\\\\


def atualiza_endereco(
    nm_logradouro,
    nr_logradouro,
    complemento,
    cep,
    id_bairro,
    cpf_cnpj,
    id_cidade,
    id_uf,
    nm_pessoa,
    id_pessoa,
    cd_endereco,
    ds_contato,
    id_contato,
):
    """atualiza endereço e contato."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE 
                PessoaEndereco 
            SET
                NmLogradouro = UPPER(RTRIM(LTRIM(SUBSTRING(?, 1, 50)))),
                NrLogradouro = RTRIM(LTRIM(SUBSTRING(?, 1, 10))),
                DsComplemento = UPPER(RTRIM(LTRIM(SUBSTRING(?, 1, 50)))),
                CdCEP = RTRIM(LTRIM(SUBSTRING(?, 1, 9))),
                IdBairro = ?,
                CdCPF_CGC = RTRIM(LTRIM(SUBSTRING(?, 1, 18))),
                IdCidade = ?,
                IdUF = ?,
                NmPessoa = RTRIM(LTRIM(SUBSTRING(?, 1, 50)))
            WHERE 
                (IdPessoa = ?) AND 
                (CdEndereco = ?)

            UPDATE 
                PessoaEndereco_Contato 
            SET 
                DsContato = RTRIM(LTRIM(SUBSTRING(?, 1, 50))),
                StContatoPrincipal = 'S'
            WHERE 
                (IdPessoaEndereco_Contato = ?) AND 
                (CdEndereco = ?)
            """,
            (
                nm_logradouro,
                nr_logradouro,
                complemento,
                cep,
                id_bairro,
                cpf_cnpj,
                id_cidade,
                id_uf,
                nm_pessoa,
                id_pessoa,
                cd_endereco,
                ds_contato,
                id_contato,
                cd_endereco,
            ),
        )
        conn.commit()
        return 1
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar dados do cliente {e}")
        return 0
    finally:
        conn.close()
