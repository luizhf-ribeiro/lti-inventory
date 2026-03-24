# LTI Inventory

Sistema web de controle de ativos de TI desenvolvido para a equipe de Tecnologia da Informação.

### Funcionalidades
- Cadastro de ativos (Notebook, Desktop, Servidor, Monitor, Impressora, etc.)
- Cadastro de usuários por setor
- Atribuição de ativos com status (Em uso, Em estoque, Em manutenção, Descartado)
- Histórico completo de movimentações
- Auditoria detalhada (quem alterou, data e hora)
- Relatórios e exportação para Excel / CSV
- Login seguro com usuário e senha

### Tecnologias utilizadas
- Python + Streamlit
- SQLite
- bcrypt (proteção de senhas)

### Como rodar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
