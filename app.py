import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import bcrypt
from PIL import Image

# ====================== CONFIGURAÇÃO COM LOGO ======================
# Carrega o logo que você subiu
try:
    logo = Image.open("logo.png")
except FileNotFoundError:
    logo = "🛠️"  # emoji de backup caso o logo não carregue

st.set_page_config(
    page_title="LTI Inventory",
    page_icon=logo,           # Seu logo aparece como ícone da aba do navegador
    layout="wide"
)

st.title("🖥️ LTI Inventory")
st.caption("Controle de Ativos de TI - Versão Web")

DB_NAME = "ativos_ti.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS ativos (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        tipo TEXT,
        marca TEXT,
        modelo TEXT,
        numero_serie TEXT UNIQUE,
        hostname TEXT,
        ip TEXT,
        status TEXT DEFAULT 'Em estoque',
        usuario_id INTEGER,
        data_compra TEXT,
        valor REAL,
        observacoes TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        setor TEXT,
        email TEXT,
        cargo TEXT,
        username TEXT UNIQUE,
        password_hash BLOB
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY,
        ativo_id INTEGER,
        usuario_id INTEGER,
        realizado_por TEXT,
        acao TEXT,
        data TEXT,
        observacoes TEXT
    )''')
    
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect(DB_NAME)

# ====================== LOGIN ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if not st.session_state.logged_in:
    st.header("🔐 Login - LTI Inventory")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT nome, password_hash FROM usuarios WHERE username = ?", (username,))
            user = c.fetchone()
            conn.close()
            if user and bcrypt.checkpw(senha.encode('utf-8'), user[1]):
                st.session_state.logged_in = True
                st.session_state.username = user[0]
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")
    st.stop()

# ====================== MENU ======================
st.sidebar.success(f"👤 Logado como: {st.session_state.username}")
menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Cadastrar Ativo", "Cadastrar Usuário", 
     "Atribuir/Atualizar Ativo", "Visualizar Ativos", 
     "Histórico", "Auditoria", "Relatórios"]
)

if st.sidebar.button("🚪 Sair"):
    st.session_state.logged_in = False
    st.rerun()

def registrar_historico(ativo_id, usuario_id, acao, observacoes=""):
    conn = get_connection()
    c = conn.cursor()
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO historico 
                 (ativo_id, usuario_id, realizado_por, acao, data, observacoes) 
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (ativo_id, usuario_id, st.session_state.username, acao, data_hora, observacoes))
    conn.commit()
    conn.close()

# ====================== DASHBOARD ======================
if menu == "Dashboard":
    st.header("Dashboard")
    conn = get_connection()
    total = pd.read_sql("SELECT COUNT(*) as cnt FROM ativos", conn).iloc[0]['cnt']
    em_uso = pd.read_sql("SELECT COUNT(*) as cnt FROM ativos WHERE status='Em uso'", conn).iloc[0]['cnt']
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Ativos", total)
    col2.metric("Em Uso", em_uso)
    col3.metric("Em Estoque", total - em_uso)
    conn.close()

# ====================== CADASTRAR ATIVO ======================
elif menu == "Cadastrar Ativo":
    st.header("Cadastrar Novo Ativo")
    with st.form("form_ativo"):
        nome = st.text_input("Nome do Ativo *")
        tipo = st.selectbox("Tipo", ["Notebook", "Desktop", "Servidor", "Monitor", "Impressora", "Switch", "Celular", "Tablet", "Outro"])
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        numero_serie = st.text_input("Número de Série *")
        hostname = st.text_input("Hostname")
        ip = st.text_input("IP")
        data_compra = st.date_input("Data de Compra", datetime.today())
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        observacoes = st.text_area("Observações")
        
        if st.form_submit_button("Cadastrar Ativo"):
            if nome and numero_serie:
                conn = get_connection()
                c = conn.cursor()
                c.execute("""INSERT INTO ativos 
                    (nome, tipo, marca, modelo, numero_serie, hostname, ip, data_compra, valor, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (nome, tipo, marca, modelo, numero_serie, hostname, ip, str(data_compra), valor, observacoes))
                ativo_id = c.lastrowid
                conn.commit()
                conn.close()
                registrar_historico(ativo_id, None, f"Cadastrado novo ativo: {nome}")
                st.success(f"Ativo {nome} cadastrado com sucesso!")
            else:
                st.error("Nome e Número de Série são obrigatórios!")

# ====================== CADASTRAR USUÁRIO ======================
elif menu == "Cadastrar Usuário":
    st.header("Cadastrar Novo Usuário")
    with st.form("form_usuario"):
        nome = st.text_input("Nome Completo *")
        setor = st.text_input("Setor *")
        email = st.text_input("E-mail")
        cargo = st.text_input("Cargo")
        username = st.text_input("Usuário (login) *")
        senha = st.text_input("Senha *", type="password")
        
        if st.form_submit_button("Cadastrar"):
            if nome and setor and username and senha:
                password_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
                conn = get_connection()
                c = conn.cursor()
                try:
                    c.execute("""INSERT INTO usuarios 
                                 (nome, setor, email, cargo, username, password_hash) 
                                 VALUES (?, ?, ?, ?, ?, ?)""",
                              (nome, setor, email, cargo, username, password_hash))
                    conn.commit()
                    st.success(f"Usuário {nome} cadastrado com sucesso!")
                except sqlite3.IntegrityError:
                    st.error("Nome de usuário já existe!")
                conn.close()
            else:
                st.error("Preencha todos os campos obrigatórios!")

# ====================== ATRIBUIR / ATUALIZAR ATIVO ======================
elif menu == "Atribuir/Atualizar Ativo":
    st.header("Atribuir ou Atualizar Ativo")
    conn = get_connection()
    ativos = pd.read_sql("SELECT id, nome, numero_serie, status FROM ativos", conn)
    usuarios = pd.read_sql("SELECT id, nome, setor FROM usuarios", conn)
    conn.close()
    
    if ativos.empty:
        st.warning("Nenhum ativo cadastrado ainda.")
    else:
        opcao = st.selectbox("Selecione o Ativo", ativos['nome'] + " - " + ativos['numero_serie'])
        ativo_id = ativos.loc[ativos['nome'] + " - " + ativos['numero_serie'] == opcao, 'id'].iloc[0]
        
        novo_status = st.selectbox("Novo Status", ["Em uso", "Em estoque", "Em manutenção", "Descartado"])
        
        usuario_id = None
        if novo_status == "Em uso" and not usuarios.empty:
            usuario_opcao = st.selectbox("Atribuir para", usuarios['nome'] + " (" + usuarios['setor'] + ")")
            usuario_id = usuarios.loc[usuarios['nome'] + " (" + usuarios['setor'] + ")" == usuario_opcao, 'id'].iloc[0]
        
        obs = st.text_area("Observações da alteração")
        
        if st.button("Salvar Alteração"):
            conn = get_connection()
            c = conn.cursor()
            if novo_status == "Em uso" and usuario_id:
                c.execute("UPDATE ativos SET status=?, usuario_id=? WHERE id=?", (novo_status, usuario_id, ativo_id))
            else:
                c.execute("UPDATE ativos SET status=?, usuario_id=NULL WHERE id=?", (novo_status, ativo_id))
            conn.commit()
            conn.close()
            
            acao = f"Status alterado para {novo_status}"
            registrar_historico(ativo_id, usuario_id, acao, obs)
            st.success("Alteração salva com sucesso!")
            st.rerun()

# ====================== VISUALIZAR ATIVOS ======================
elif menu == "Visualizar Ativos":
    st.header("Lista de Ativos")
    conn = get_connection()
    df = pd.read_sql("""SELECT a.*, u.nome as usuario, u.setor 
                        FROM ativos a LEFT JOIN usuarios u ON a.usuario_id = u.id""", conn)
    conn.close()
    
    busca = st.text_input("Buscar por nome, série, hostname ou IP")
    if busca:
        df = df[df.apply(lambda row: busca.lower() in str(row).lower(), axis=1)]
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    col1, col2 = st.columns(2)
    col1.download_button("📥 Baixar CSV", df.to_csv(index=False), "ativos.csv", "text/csv")
    
    with pd.ExcelWriter("ativos.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    with open("ativos.xlsx", "rb") as f:
        col2.download_button("📥 Baixar Excel", f, "ativos.xlsx")

# ====================== HISTÓRICO ======================
elif menu == "Histórico":
    st.header("Histórico de Movimentações")
    conn = get_connection()
    hist = pd.read_sql("""SELECT h.data, h.realizado_por, a.nome as ativo, h.acao, h.observacoes 
                          FROM historico h 
                          LEFT JOIN ativos a ON h.ativo_id = a.id 
                          ORDER BY h.data DESC""", conn)
    conn.close()
    st.dataframe(hist, use_container_width=True, hide_index=True)

# ====================== AUDITORIA ======================
elif menu == "Auditoria":
    st.header("🔍 Auditoria de Alterações")
    conn = get_connection()
    audit = pd.read_sql("""SELECT data, realizado_por as analista, acao, observacoes 
                           FROM historico ORDER BY data DESC""", conn)
    conn.close()
    st.dataframe(audit, use_container_width=True, hide_index=True)

# ====================== RELATÓRIOS ======================
elif menu == "Relatórios":
    st.header("Relatórios")
    conn = get_connection()
    st.subheader("Ativos por Tipo")
    st.dataframe(pd.read_sql("SELECT tipo, COUNT(*) as quantidade FROM ativos GROUP BY tipo", conn))
    conn.close()

st.sidebar.info("LTI Inventory v3.0 - Versão Web")
