import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
import time
import os
import hashlib
from pathlib import Path

# --- 1. CONFIGURAÇÕES E CONSTANTES ---
CONFIG = {
    "APP_NAME": "Thiago Castro Advogados",
    "PAGE_TITLE": "Portal | Thiago Castro Advogados",
    "DB_NAME": "dados_escritorio.db",
    "UPLOAD_DIR": "arquivos_processos",
    "COLORS": {
        "GOLD": "#Cea065",
        "BG": "#00202f",
        "SIDEBAR": "#00202f"
    }
}

st.set_page_config(
    page_title=CONFIG["PAGE_TITLE"],
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- 2. GERENCIADORES (SERVICES/DAOs) ---

class Utils:
    """Utilitários gerais e de segurança."""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove caminhos relativos para evitar ataques."""
        return os.path.basename(filename)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash simples para demonstração."""
        return hashlib.sha256(password.encode()).hexdigest()

class FileManager:
    """Responsável pela manipulação segura de arquivos."""
    
    @staticmethod
    def save_files(uploaded_files, protocol_id: int, uploader_type: str):
        if not uploaded_files:
            return
            
        # Cria estrutura: arquivos_processos/123/cliente/
        base_path = Path(CONFIG["UPLOAD_DIR"]) / str(protocol_id) / uploader_type
        base_path.mkdir(parents=True, exist_ok=True)
        
        for file in uploaded_files:
            safe_name = Utils.sanitize_filename(file.name)
            file_path = base_path / safe_name
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())

    @staticmethod
    def list_files(protocol_id: int, uploader_type: str):
        base_path = Path(CONFIG["UPLOAD_DIR"]) / str(protocol_id) / uploader_type
        if base_path.exists() and any(base_path.iterdir()):
            st.markdown(f"📂 **Anexos ({uploader_type}):**")
            for file_path in base_path.iterdir():
                if file_path.is_file():
                    with open(file_path, "rb") as f:
                        st.download_button(
                            f"⬇️ Baixar {file_path.name}", 
                            f, 
                            file_name=file_path.name,
                            key=f"dl_{protocol_id}_{uploader_type}_{file_path.name}"
                        )
        else:
            st.caption(f"Sem anexos de {uploader_type}.")

class DatabaseManager:
    """Gerencia conexões e queries de forma segura."""
    
    def __init__(self, db_name: str):
        self.db_name = db_name
        self._init_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _init_tables(self):
        """Inicializa esquema do banco."""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS chamados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_nome TEXT, telefone TEXT, descricao TEXT,
                    data_abertura TEXT, resposta_interna TEXT,
                    resposta_publica TEXT, responsavel TEXT, status TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    username TEXT PRIMARY KEY, senha TEXT, nome TEXT, funcao TEXT
                )
            ''')
            # Usuário Admin Padrão (Senha: 1234)
            admin_pass = Utils.hash_password("1234")
            c.execute("INSERT OR IGNORE INTO usuarios VALUES (?, ?, ?, ?)", 
                      ('Thiago Castro', admin_pass, 'Dr. Thiago Castro', 'Sócio-Proprietário'))

    def execute_query(self, query: str, params: tuple = ()):
        """Executa comandos de modificação (INSERT, UPDATE, DELETE)."""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.lastrowid

    def fetch_data(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """Executa comandos de leitura e retorna DataFrame."""
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def fetch_one(self, query: str, params: tuple = ()):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.fetchone()

# Instância global do DB
db = DatabaseManager(CONFIG["DB_NAME"])

# --- 3. CSS E ESTILIZAÇÃO VISUAL ---

def inject_custom_css():
    st.markdown(f"""
        <style>
        /* Variáveis */
        :root {{ --primary-color: {CONFIG['COLORS']['GOLD']}; }}
        
        /* Layout Base */
        [data-testid="stAppViewContainer"] {{ background-color: {CONFIG['COLORS']['BG']}; color: white; }}
        [data-testid="stSidebar"] {{ background-color: {CONFIG['COLORS']['SIDEBAR']}; border-right: 1px solid {CONFIG['COLORS']['GOLD']}; }}
        
        /* Centralizar Logo */
        [data-testid="stImage"] {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin-bottom: 20px;
        }}
        [data-testid="stImage"] > img {{
            object-fit: contain;
            max-width: 250px;
        }}

        /* PADRONIZAÇÃO DOS BOTÕES */
        div.stButton {{
            width: 100%;
            display: flex;
            justify-content: center;
        }}
        
        /* Botão Padrão */
        div.stButton > button {{
            width: 100% !important;
            max-width: 350px !important; /* Limite para Desktop */
            height: 60px !important;
            background-color: {CONFIG['COLORS']['GOLD']} !important;
            color: #00202f !important;
            font-weight: 800 !important;
            font-size: 18px !important;
            border-radius: 12px !important;
            border: none !important;
        }}
        div.stButton > button:hover {{
            background-color: #b38b52 !important;
            transform: scale(1.02);
            transition: all 0.2s ease-in-out;
        }}

        /* Botão Secundário (Estilo Outline) */
        button[kind="secondary"] {{
            background: transparent !important;
            border: 2px solid {CONFIG['COLORS']['GOLD']} !important;
            color: {CONFIG['COLORS']['GOLD']} !important;
        }}
        button[kind="secondary"]:hover {{
            border-color: white !important;
            color: white !important;
        }}
        
        /* Inputs e Textos */
        h1, h2, h3 {{ color: {CONFIG['COLORS']['GOLD']} !important; text-align: center; }}
        p, label {{ color: white !important; }}
        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div {{
            background-color: white !important;
            border: 2px solid {CONFIG['COLORS']['GOLD']} !important;
            border-radius: 8px !important;
        }}
        input, textarea {{ color: black !important; }}
        </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown(f"## {CONFIG['APP_NAME']}")
        
        if st.session_state.get('usuario_logado'):
            st.info(f"Logado: {st.session_state['usuario_logado']}\nCargo: {st.session_state['funcao_usuario']}")
            if st.button("SAIR"):
                st.session_state.clear()
                st.rerun()

# --- 4. TELAS (VIEWS) ---

def view_login_screen():
    # 1. Logo (Centralização via CSS)
    try:
        st.image("logo.png")
    except:
        st.markdown(f"<h1>{CONFIG['APP_NAME']}</h1>", unsafe_allow_html=True)
    
    st.write("")
    
    if 'tipo_acesso' not in st.session_state:
        st.markdown("<h3>Seja bem-vindo(a)</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; opacity: 0.8;'>Selecione seu perfil de acesso</p>", unsafe_allow_html=True)
        st.write("")
        
        # Centralização dos Botões via Colunas
        col_esq, col_meio, col_dir = st.columns([0.1, 0.8, 0.1])
        with col_meio:
            if st.button("Sou Cliente"):
                st.session_state['tipo_acesso'] = 'cliente'
                st.rerun()
            
            st.write("") # Espaço entre botões
            
            if st.button("Sou Advogado"):
                st.session_state['tipo_acesso'] = 'interno'
                st.rerun()
        return

    # Tela Cliente
    if st.session_state['tipo_acesso'] == 'cliente':
        col_esq, col_meio, col_dir = st.columns([0.1, 0.8, 0.1])
        with col_meio:
            if st.button("⬅ Voltar", type="secondary"):
                del st.session_state['tipo_acesso']
                st.rerun()
        view_client_area()

    # Tela Login Interno
    elif st.session_state['tipo_acesso'] == 'interno':
        col_esq, col_meio, col_dir = st.columns([0.1, 0.8, 0.1])
        with col_meio:
            if st.button("⬅ Voltar", type="secondary"):
                del st.session_state['tipo_acesso']
                st.rerun()
        
        st.markdown("<h3 style='margin-top:20px;'>Login Corporativo</h3>", unsafe_allow_html=True)
        
        # Formulário Centralizado
        c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
        with c2:
            with st.form("login_form"):
                user = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                st.write("")
                if st.form_submit_button("Entrar"):
                    hashed_pw = Utils.hash_password(password)
                    user_data = db.fetch_one("SELECT nome, funcao FROM usuarios WHERE username = ? AND senha = ?", (user, hashed_pw))
                    
                    if user_data:
                        st.session_state['usuario_logado'] = user_data[0]
                        st.session_state['funcao_usuario'] = user_data[1]
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")

def view_client_area():
    st.write("")
    tab1, tab2 = st.tabs(["Novo Pedido", "Consultar"])
    
    with tab1:
        with st.form("new_request"):
            nome = st.text_input("Nome Completo")
            tel = st.text_input("WhatsApp")
            desc = st.text_area("Descrição do Caso")
            files = st.file_uploader("Anexar Documentos", accept_multiple_files=True)
            st.write("")
            if st.form_submit_button("Enviar Solicitação"):
                if nome and desc:
                    row_id = db.execute_query(
                        "INSERT INTO chamados (cliente_nome, telefone, descricao, data_abertura, resposta_publica, responsavel, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (nome, tel, desc, datetime.now().strftime("%d/%m/%Y"), "", "Sem Responsável", "Aberto")
                    )
                    FileManager.save_files(files, row_id, "cliente")
                    st.success(f"✅ Protocolo gerado: #{row_id}")
                    st.balloons()
                else:
                    st.warning("Preencha o nome e a descrição.")
    
    with tab2:
        prot = st.number_input("Número do Protocolo", min_value=1, step=1)
        if st.button("Pesquisar"):
            df = db.fetch_data("SELECT * FROM chamados WHERE id = ?", (prot,))
            if not df.empty:
                row = df.iloc[0]
                st.markdown(f"**Status:** {row['status']}")
                FileManager.list_files(prot, "cliente")
                st.divider()
                if row['resposta_publica']:
                    st.markdown(f"<div style='background-color:#00161F; padding:15px; border:1px solid {CONFIG['COLORS']['GOLD']}; border-radius:5px;'>{row['resposta_publica']}</div>", unsafe_allow_html=True)
                    FileManager.list_files(prot, "advogado")
                else:
                    st.info("⏳ Aguardando análise do escritório.")
            else:
                st.error("Protocolo não encontrado.")

def view_admin_dashboard():
    # Header Painel
    st.markdown(f"<h3>Painel | {st.session_state['usuario_logado']}</h3>", unsafe_allow_html=True)
    
    if st.session_state['funcao_usuario'] == 'Sócio-Proprietário':
        tabs = st.tabs(["📊 Visão", "📌 Triagem", "✅ Validar", "👥 Equipe"])
        
        with tabs[0]: # Dashboard
            df = db.fetch_data("SELECT id, cliente_nome, status, responsavel FROM chamados")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total", len(df))
            col2.metric("Pendentes", len(df[df['status']=='Aberto']))
            col3.metric("Concluídos", len(df[df['status']=='Concluído']))
            st.dataframe(df, use_container_width=True, hide_index=True)

        with tabs[1]: # Triagem
            _render_triagem()
            
        with tabs[2]: # Validação
            _render_validacao()

        with tabs[3]: # Equipe
            _render_team_management()
    else:
        # Visão Advogado/Staff
        _render_staff_tasks()

# --- 5. COMPONENTES AUXILIARES (ADMIN) ---

def _render_triagem():
    df = db.fetch_data("SELECT * FROM chamados WHERE status='Aberto'")
    staff_df = db.fetch_data("SELECT nome FROM usuarios WHERE funcao != 'Sócio-Proprietário'")
    staff_list = staff_df['nome'].tolist()
    
    if df.empty:
        st.success("Fila de triagem zerada.")
        return

    for _, row in df.iterrows():
        with st.expander(f"Caso #{row['id']} - {row['cliente_nome']}", expanded=True):
            st.info(row['descricao'])
            FileManager.list_files(row['id'], "cliente")
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                assignee = st.selectbox("Delegar para:", staff_list, key=f"sel_{row['id']}")
                if st.button("Delegar", key=f"btn_del_{row['id']}"):
                    db.execute_query("UPDATE chamados SET responsavel = ?, status = 'Em Análise' WHERE id = ?", (assignee, row['id']))
                    st.rerun()
            with c2:
                resp = st.text_area("Resposta Direta (Sócio)", key=f"resp_{row['id']}")
                files = st.file_uploader("Anexar", key=f"up_socio_{row['id']}", accept_multiple_files=True)
                if st.button("Finalizar Caso", key=f"btn_fin_{row['id']}"):
                    db.execute_query("UPDATE chamados SET resposta_publica = ?, status = 'Concluído', responsavel = 'Sócio-Proprietário' WHERE id = ?", (resp, row['id']))
                    FileManager.save_files(files, row['id'], "advogado")
                    st.rerun()

def _render_validacao():
    df = db.fetch_data("SELECT * FROM chamados WHERE status='Pendente Aprovação'")
    if df.empty:
        st.info("Nenhuma minuta aguardando validação.")
        return
        
    for _, row in df.iterrows():
        with st.expander(f"#{row['id']} (Resp: {row['responsavel']})", expanded=True):
            st.markdown(f"**Cliente:** {row['descricao']}")
            st.markdown(f"**Minuta Sugerida:**\n> {row['resposta_interna']}")
            FileManager.list_files(row['id'], "advogado")
            
            new_text = st.text_area("Edição Final", value=row['resposta_interna'], key=f"val_{row['id']}")
            
            if st.button("Aprovar e Enviar ao Cliente", key=f"apr_{row['id']}"):
                db.execute_query("UPDATE chamados SET resposta_publica = ?, status = 'Concluído' WHERE id = ?", (new_text, row['id']))
                st.rerun()

def _render_team_management():
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Novo Membro")
        with st.form("add_user"):
            u = st.text_input("Login")
            p = st.text_input("Senha", type="password")
            n = st.text_input("Nome")
            r = st.selectbox("Cargo", ["Advogado", "Estagiário"])
            if st.form_submit_button("Cadastrar"):
                try:
                    hashed = Utils.hash_password(p)
                    db.execute_query("INSERT INTO usuarios VALUES (?, ?, ?, ?)", (u, hashed, n, r))
                    st.success("Usuário criado!")
                except:
                    st.error("Erro: Login já existe.")
    
    with c2:
        st.subheader("Equipe Atual")
        users = db.fetch_data("SELECT nome, username, funcao FROM usuarios")
        st.dataframe(users, hide_index=True)

def _render_staff_tasks():
    user = st.session_state['usuario_logado']
    df = db.fetch_data("SELECT * FROM chamados WHERE responsavel = ? AND status != 'Concluído'", (user,))
    
    st.subheader("Minhas Tarefas Pendentes")
    if df.empty:
        st.success("Você não tem tarefas pendentes.")
        return

    for _, row in df.iterrows():
        with st.container(border=True):
            st.markdown(f"**Caso #{row['id']}** - {row['cliente_nome']}")
            st.write(row['descricao'])
            FileManager.list_files(row['id'], "cliente")
            
            if row['status'] == 'Pendente Aprovação':
                st.warning("⏳ Minuta enviada. Aguardando validação do Sócio.")
            else:
                resp = st.text_area("Minuta de Resposta", key=f"my_{row['id']}")
                files = st.file_uploader("Anexos Internos", key=f"up_{row['id']}", accept_multiple_files=True)
                if st.button("Enviar para Validação", key=f"snd_{row['id']}"):
                    db.execute_query("UPDATE chamados SET resposta_interna = ?, status = 'Pendente Aprovação' WHERE id = ?", (resp, row['id']))
                    FileManager.save_files(files, row['id'], "advogado")
                    st.rerun()

# --- 6. EXECUÇÃO PRINCIPAL ---

def main():
    inject_custom_css()
    render_sidebar()
    
    if 'usuario_logado' not in st.session_state or not st.session_state['usuario_logado']:
        view_login_screen()
    else:
        view_admin_dashboard()

if __name__ == "__main__":
    main()
