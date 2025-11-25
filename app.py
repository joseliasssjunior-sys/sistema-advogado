import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
import hashlib
from pathlib import Path
import base64

# --- 1. CONFIGURAÇÕES ---
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

# --- 2. GERENCIADORES (BACKEND) ---

class Utils:
    @staticmethod
    def get_image_base64(path):
        try:
            with open(path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
        except:
            return None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        return os.path.basename(filename)

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

class FileManager:
    @staticmethod
    def save_files(uploaded_files, protocol_id: int, uploader_type: str):
        if not uploaded_files: return
        base_path = Path(CONFIG["UPLOAD_DIR"]) / str(protocol_id) / uploader_type
        base_path.mkdir(parents=True, exist_ok=True)
        for file in uploaded_files:
            safe_name = Utils.sanitize_filename(file.name)
            with open(base_path / safe_name, "wb") as f:
                f.write(file.getbuffer())

    @staticmethod
    def list_files(protocol_id: int, uploader_type: str):
        base_path = Path(CONFIG["UPLOAD_DIR"]) / str(protocol_id) / uploader_type
        if base_path.exists() and any(base_path.iterdir()):
            st.markdown(f"📂 **Anexos ({uploader_type}):**")
            for file_path in base_path.iterdir():
                if file_path.is_file():
                    with open(file_path, "rb") as f:
                        st.download_button(f"⬇️ Baixar {file_path.name}", f, file_name=file_path.name, key=f"dl_{protocol_id}_{uploader_type}_{file_path.name}")

class DatabaseManager:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self._init_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _init_tables(self):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS chamados (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_nome TEXT, telefone TEXT, descricao TEXT, data_abertura TEXT, resposta_interna TEXT, resposta_publica TEXT, responsavel TEXT, status TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY, senha TEXT, nome TEXT, funcao TEXT)''')
            admin_pass = Utils.hash_password("1234")
            c.execute("INSERT OR IGNORE INTO usuarios VALUES (?, ?, ?, ?)", ('Thiago Castro', admin_pass, 'Dr. Thiago Castro', 'Sócio-Proprietário'))

    def execute_query(self, query: str, params: tuple = ()):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.lastrowid

    def fetch_data(self, query: str, params: tuple = ()) -> pd.DataFrame:
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def fetch_one(self, query: str, params: tuple = ()):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.fetchone()

db = DatabaseManager(CONFIG["DB_NAME"])

# --- 3. CSS (Correções Visuais) ---

def inject_custom_css():
    st.markdown(f"""
        <style>
        :root {{ --primary-color: {CONFIG['COLORS']['GOLD']}; }}
        
        [data-testid="stAppViewContainer"] {{ background-color: {CONFIG['COLORS']['BG']}; color: white; }}
        [data-testid="stSidebar"] {{ background-color: {CONFIG['COLORS']['SIDEBAR']}; border-right: 1px solid {CONFIG['COLORS']['GOLD']}; }}
        
        h1, h2, h3 {{ color: {CONFIG['COLORS']['GOLD']} !important; text-align: center; }}
        p, label {{ color: white !important; }}

        /* --- BOTÕES GERAIS E DE FORMULÁRIO --- */
        /* Alvo: Botões normais E Botões de Formulário */
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button {{
            width: 80vw !important; /* 80% da tela mobile */
            max-width: 350px !important; /* Trava no PC */
            height: 55px !important;
            
            /* Centralização */
            display: block !important;
            margin-left: auto !important;
            margin-right: auto !important;
            
            /* Estilo */
            background-color: {CONFIG['COLORS']['GOLD']} !important;
            color: #00202f !important; /* Texto Azul Escuro */
            border: none !important;
            border-radius: 12px !important;
            font-weight: 800 !important;
            font-size: 16px !important;
            text-transform: uppercase !important;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.2) !important;
        }}

        /* Centralizar o container do botão */
        div.stButton, div[data-testid="stFormSubmitButton"] {{
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            margin-bottom: 10px !important;
        }}

        /* Hover */
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {{
            background-color: #b38b52 !important;
            transform: scale(1.02);
            color: white !important;
        }}

        /* --- INPUTS E SENHA --- */
        
        /* Caixa do Input (Fundo Branco, Borda Dourada) */
        div[data-baseweb="input"] {{
            background-color: white !important;
            border: 2px solid {CONFIG['COLORS']['GOLD']} !important;
            border-radius: 8px !important;
        }}
        
        /* Texto digitado dentro do input */
        input {{
            color: #00202f !important; /* Texto escuro para contraste */
            font-weight: bold !important;
        }}

        /* --- CORREÇÃO DO ÍCONE DO OLHO (SENHA) --- */
        /* O botão do olho estava branco no fundo branco. Vamos pintar de azul escuro. */
        button[aria-label="Password visibility"] {{
            color: #00202f !important; /* Cor do ícone */
        }}
        button[aria-label="Password visibility"]:hover {{
            color: {CONFIG['COLORS']['GOLD']} !important;
        }}

        header {{ visibility: hidden; }}
        </style>
    """, unsafe_allow_html=True)

def render_logo_html():
    img_b64 = Utils.get_image_base64("logo.png")
    if img_b64:
        st.markdown(f"""
            <div style="display: flex; justify-content: center; margin-bottom: 30px;">
                <img src="{img_b64}" style="max-width: 280px; width: 70%; object-fit: contain;">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<h1>{CONFIG['APP_NAME']}</h1>", unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        render_logo_html()
        if st.session_state.get('usuario_logado'):
            st.info(f"Logado: {st.session_state['usuario_logado']}")
            if st.button("SAIR"):
                st.session_state.clear()
                st.rerun()

# --- 4. TELAS ---

def view_login_screen():
    render_logo_html()
    
    if 'tipo_acesso' not in st.session_state:
        st.markdown("<h3>Seja bem-vindo(a)</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; opacity: 0.8; margin-bottom: 40px;'>Selecione seu perfil de acesso</p>", unsafe_allow_html=True)
        
        if st.button("SOU CLIENTE"):
            st.session_state['tipo_acesso'] = 'cliente'
            st.rerun()
        
        if st.button("SOU ADVOGADO"):
            st.session_state['tipo_acesso'] = 'interno'
            st.rerun()
            
        return

    # Tela Cliente
    if st.session_state['tipo_acesso'] == 'cliente':
        if st.button("⬅ VOLTAR"):
            del st.session_state['tipo_acesso']
            st.rerun()
        view_client_area()

    # Tela Login Interno
    elif st.session_state['tipo_acesso'] == 'interno':
        if st.button("⬅ VOLTAR"):
            del st.session_state['tipo_acesso']
            st.rerun()
        
        st.markdown("<h3 style='margin-top:20px;'>Login Corporativo</h3>", unsafe_allow_html=True)
        
        # Formulário
        c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
        with c2:
            with st.form("login_form"):
                user = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                st.write("")
                
                # A correção CSS agora pega especificamente este botão
                if st.form_submit_button("ENTRAR"):
                    hashed_pw = Utils.hash_password(password)
                    user_data = db.fetch_one("SELECT nome, funcao FROM usuarios WHERE username = ? AND senha = ?", (user, hashed_pw))
                    if user_data:
                        st.session_state['usuario_logado'] = user_data[0]
                        st.session_state['funcao_usuario'] = user_data[1]
                        st.rerun()
                    else:
                        st.error("Acesso negado.")

def view_client_area():
    st.write("")
    tab1, tab2 = st.tabs(["Novo Pedido", "Consultar"])
    with tab1:
        with st.form("new_request"):
            nome = st.text_input("Nome Completo")
            tel = st.text_input("WhatsApp")
            desc = st.text_area("Descrição do Caso")
            files = st.file_uploader("Documentos", accept_multiple_files=True)
            st.write("")
            if st.form_submit_button("ENVIAR SOLICITAÇÃO"):
                if nome and desc:
                    row_id = db.execute_query("INSERT INTO chamados (cliente_nome, telefone, descricao, data_abertura, resposta_publica, responsavel, status) VALUES (?, ?, ?, ?, ?, ?, ?)", (nome, tel, desc, datetime.now().strftime("%d/%m/%Y"), "", "Sem Responsável", "Aberto"))
                    FileManager.save_files(files, row_id, "cliente")
                    st.success(f"Protocolo: #{row_id}")
                else:
                    st.warning("Preencha os dados.")
    with tab2:
        prot = st.number_input("Protocolo", min_value=1, step=1)
        if st.button("PESQUISAR"):
            df = db.fetch_data("SELECT * FROM chamados WHERE id = ?", (prot,))
            if not df.empty:
                row = df.iloc[0]
                st.write(f"**Status:** {row['status']}")
                if row['resposta_publica']:
                    st.info(f"Resposta: {row['resposta_publica']}")
                    FileManager.list_files(prot, "advogado")
                else:
                    st.warning("Em análise.")
            else:
                st.error("Não encontrado.")

def view_admin_dashboard():
    st.markdown(f"<h3>Painel | {st.session_state['usuario_logado']}</h3>", unsafe_allow_html=True)
    if st.session_state['funcao_usuario'] == 'Sócio-Proprietário':
        t1, t2, t3, t4 = st.tabs(["📊 Visão", "📌 Triagem", "✅ Validar", "👥 Equipe"])
        with t1:
            df = db.fetch_data("SELECT id, cliente_nome, status, responsavel FROM chamados")
            st.metric("Total", len(df))
            st.dataframe(df, use_container_width=True, hide_index=True)
        with t2: _render_triagem()
        with t3: _render_validacao()
        with t4: _render_team_management()
    else:
        _render_staff_tasks()

def _render_triagem():
    df = db.fetch_data("SELECT * FROM chamados WHERE status='Aberto'")
    staff = db.fetch_data("SELECT nome FROM usuarios WHERE funcao != 'Sócio-Proprietário'")['nome'].tolist()
    if df.empty: st.success("Limpo."); return
    for _, row in df.iterrows():
        with st.expander(f"#{row['id']} - {row['cliente_nome']}", expanded=True):
            st.write(row['descricao'])
            c1, c2 = st.columns(2)
            with c1:
                sel = st.selectbox("Delegar", staff, key=f"s_{row['id']}")
                if st.button("Confirmar", key=f"d_{row['id']}"):
                    db.execute_query("UPDATE chamados SET responsavel = ?, status = 'Em Análise' WHERE id = ?", (sel, row['id']))
                    st.rerun()
            with c2:
                if st.button("Finalizar", key=f"f_{row['id']}"):
                    db.execute_query("UPDATE chamados SET status = 'Concluído', responsavel = 'Sócio' WHERE id = ?", (row['id'],))
                    st.rerun()

def _render_validacao():
    df = db.fetch_data("SELECT * FROM chamados WHERE status='Pendente Aprovação'")
    if df.empty: st.info("Vazio."); return
    for _, row in df.iterrows():
        st.write(f"Minuta: {row['resposta_interna']}")
        if st.button(f"Aprovar #{row['id']}"):
            db.execute_query("UPDATE chamados SET resposta_publica = ?, status = 'Concluído' WHERE id = ?", (row['resposta_interna'], row['id']))
            st.rerun()

def _render_team_management():
    with st.form("new_u"):
        u = st.text_input("User"); p = st.text_input("Pass", type="password"); n = st.text_input("Nome"); c = st.selectbox("Cargo", ["Advogado", "Estagiário"])
        if st.form_submit_button("Criar"):
            try:
                db.execute_query("INSERT INTO usuarios VALUES (?,?,?,?)", (u, Utils.hash_password(p), n, c))
                st.success("Criado")
            except: st.error("Erro")
    st.dataframe(db.fetch_data("SELECT nome, username FROM usuarios"), use_container_width=True)

def _render_staff_tasks():
    user = st.session_state['usuario_logado']
    df = db.fetch_data("SELECT * FROM chamados WHERE responsavel = ? AND status != 'Concluído'", (user,))
    if df.empty: st.success("Sem tarefas."); return
    for _, row in df.iterrows():
        with st.container(border=True):
            st.markdown(f"**#{row['id']}**"); st.write(row['descricao'])
            resp = st.text_area("Resposta", key=f"r_{row['id']}")
            if st.button("Enviar", key=f"b_{row['id']}"):
                db.execute_query("UPDATE chamados SET resposta_interna = ?, status = 'Pendente Aprovação' WHERE id = ?", (resp, row['id']))
                st.rerun()

def main():
    inject_custom_css()
    render_sidebar()
    if not st.session_state.get('usuario_logado'):
        view_login_screen()
    else:
        view_admin_dashboard()

if __name__ == "__main__":
    main()
