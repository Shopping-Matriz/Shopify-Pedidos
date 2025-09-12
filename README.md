# 🔰 Integrador de Pedidos Alterdata ↔ Shopify

Este projeto realiza a integração entre o sistema **Alterdata** e a plataforma **Shopify**, espelhando os pedidos de venda do **Shopify** no **Alterdata** (cadastrando mo módulo Pedido de venda).

---

## 🚀 Funcionalidades
- Consulta de dados no banco **ALTERDATA** via `pyodbc`.
- Mapeamento automático dos pedidos pagos e prontos para integração.
- Criação de tags para separação de pedidos já integrados ("✔ Integrado") e pedidos para serem verificados ("💳 Verificar") na Shopify.
- Verificação extra do CEP com a API do **Viacep.com.br**.
- Execução contínua em loop com intervalo de 10 minutos (customizável) e logs no Terminal.
- Possibilidade de virar um executável para fácil implementação.

---

## 📋 Pré-requisitos

- **Python 3.9+** instalado  
- Banco de dados **SQL Server** acessível  
- Instalação do driver ODBC para SQL Server  
- Bibliotecas Python necessárias:  
  ```bash
  pip install -r requirements.txt
  ```

---

## ▶ Executando manualmente

1. Clone ou copie os arquivos do projeto.
2. Configure as credenciais do banco de dados e do Shopify no seu arquivo **.env** :
   ```python
    SHOPIFY_API_URL= "Seu link aqui"
    SHOPIFY_ACCESS_TOKEN= "Seu token aqui"
    DB_DRIVER= ODBC Driver 17 (ou 18) for SQL Server 
    DB_SERVER= "Seu Server,Porta"
    DB_DATABASE= "Nome do banco"
    DB_USERNAME= "Usuário do banco"
    DB_PASSWORD= "Senha do usuário"
   ```
3. Execute o script no terminal:
   ```bash
   python main.py
   ```
   ou no Windows:
   ```cmd
   py main.py
   ```

---

## ⚙ Gerando um executável (.exe)

Caso queira rodar sem depender do Python instalado:

1. Instale o **PyInstaller**:
   ```bash
   pip install pyinstaller
   ```
2. Gere o executável:
   ```bash
   pyinstaller --onefile main.py
   ```
3. O executável será criado em:
   ```
   dist/main.exe
   ```
4. Para rodar:
   ```cmd
   dist\main.exe
   ```

---

## 📌 Observações

- O script roda em **loop infinito**, verificando os pedidos prontos para integração a cada **10 minutos**.  
- Para rodar em segundo plano, recomenda-se:
  - Usar o **Agendador de Tarefas do Windows**  
  - Ou configurar como um **serviço do Windows/Linux**  
- Certifique-se de que o **driver ODBC do SQL Server** esteja instalado na máquina que executará o integrador.  
- Dependências adicionais podem ser incluídas no `requirements.txt` para facilitar instalação em novos ambientes.  

---

## 🛠 Estrutura recomendada
```
📂 raiz/
 ├── main.py                # Código principal
 ├── shopify_service.py     # Chamadas para API da Shopify em GrathQL
 ├── alterdata_service.py   # Conexão + Queries Para o ALTERDATA 
 ├── auxiliar.py            # Funções auxiliares  
 ├── config.py              # Código de configuração (Usa os dados do .env)
 ├── cod_pegamento_aux.txt  # Rascunho para Importação dos pagamentos 
 ├── README.md              # Este arquivo
 └── requirements.txt       # Dependências (requests, pyodbc)[Se existir]
```
