import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
import time
import os

# --- 1. CONFIGURAÇÕES GERAIS ---
NOME_ESCRITORIO = "Thiago Castro Advogados"
TITULO_ABA = "Portal | Thiago Castro Advogados"

# Cores Dark Luxury
COR_DOURADO = "#Cea065"
COR_FUNDO = "#00202f"
COR_INPUT = "#00161F"

st.set_page_config(
    page_title=TITULO_ABA, 
    page_icon="⚖️", 
    layout="centered", # Mudei para CENTERED para ficar melhor no celular
    initial_sidebar_state="collapsed"
)

# --- 2. FUNÇÕES DE ARQUIVOS ---
def salvar_arquivos(uploaded_files, id_protocolo, quem_enviou):
    if not uploaded_files:
        return
    pasta_destino = f"arquivos_processos/{id_protocolo}/{quem_enviou}"
    os.makedirs(pasta_destino, exist_ok=True)
    for uploaded_file in uploaded_files:
        caminho_completo = os.path.join(pasta_destino, uploaded_file.name)
        with open(caminho_completo, "wb") as f:
            f.write(uploaded_file.getbuffer())

def listar_arquivos_download(id_protocolo, quem_enviou):
    pasta = f"arquivos_processos/{id_protocolo}/{quem_enviou}"
    if os.path.exists(pasta):
        arquivos = os.listdir(pasta)
        if arquivos:
            st.markdown(f"📂 **Anexos ({quem_enviou}):**")
            for arq in arquivos:
                caminho = os.path.join(pasta, arq)
                with open(caminho, "rb") as f:
                    st.download_button(f"⬇️ Baixar {arq}", f, file_name=arq)

# --- 3. CSS ESTILIZADO (LAYOUT MOBILE) ---
def configurar_estilo_visual():
    st.markdown(f"""
        <style>
        :root {{ --primary-color: {COR_DOURADO}; }}
        
        /* Esconde Menu Hambúrguer e Barra Superior */
        header {{ visibility: hidden; }}
        [data-testid="stSidebarCollapsedControl"] {{ display: none; }}
        
        /* Fundo Geral */
        .stApp {{
            background-color: {COR_FUNDO};
            color: white;
        }}
        
        /* Logo Centralizada */
        [data-testid="stImage"] {{
            display: flex;
            justify-content: center;
        }}
        
        /* Botões Dourados */
        [data-testid="stFormSubmitButton"] > button,
        [data-testid="baseButton-primary"] {{
            background-color: {COR_DOURADO} !important;
            color: black !important;
            border: none !important;
            font-weight: bold !important;
            width: 100%; /* Botão ocupa largura total no celular */
        }}
        
        /* Inputs e Selects */
        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div {{
            background-color: {COR_INPUT} !important;
            border: 1px solid {COR_DOURADO} !important;
            color: white !important;
            border-radius: 8px !important;
        }}
        input {{ color: white !important; }}
        
        /* Correção Senha */
        button[aria-label="Password visibility"] {{ color: {COR_DOURADO} !important; }}
        
        /* Abas (Tabs) */
        .stTabs [data-baseweb="tab-highlight"] {{ background-color: {COR_DOURADO} !important; }}
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{ color: {COR_DOURADO} !important; }}
        
        /* Radio Button Horizontal (Menu Topo) */
        div[role="radiogroup"] {{
            display: flex;
            justify-content: center;
            background-color: {COR_INPUT};
            padding: 10px;
            border-radius: 10px;
            border: 1px solid {COR_DOURADO};
            margin-bottom: 20px;
        }}
        div[role="radiogroup"] label {{
            color: white !important;
            font-weight: bold;
        }}
        div[role="radiogroup"] > label > div:first-child {{
            background-color: {COR_DOURADO} !important;
            border-color: {COR_DOURADO} !important;
        }}
        
        </style>
    """, unsafe_allow_html=True)

configurar_estilo_visual()

# --- 4. BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('dados_escritorio.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nome TEXT,
            telefone TEXT,
            descricao TEXT,
            data_abertura TEXT,
            resposta_interna TEXT,
            resposta_publica TEXT,
            responsavel TEXT,
            status TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            senha TEXT,
            nome TEXT,
            funcao TEXT
        )
    ''')
    c.execute("SELECT * FROM usuarios WHERE username = 'Thiago Castro'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios VALUES ('Thiago Castro', '1234', 'Dr. Thiago Castro', 'Sócio-Proprietário')")
    conn.commit()
    conn.close()

init_db()

# --- 5. CABEÇALHO (HEADER) ---
def header_app():
    # Mostra a Logo Centralizada
    try:
        logo = Image.open("logo.png")
        st.image(logo, width=200) # Tamanho ideal pro celular
    except:
        st.title(NOME_ESCRITORIO)
    
    st.write("")

# --- 6. LÓGICA DO SISTEMA ---
if 'usuario_logado' not in st.session_state:
    st.session_state['usuario_logado'] = None
if 'funcao_usuario' not in st.session_state:
    st.session_state['funcao_usuario'] = None

header_app()

# === MODO DESLOGADO (PÚBLICO) ===
if st.session_state['usuario_logado'] is None:
    
    # Menu Horizontal no Topo (Estilo App)
    menu_publico = st.radio("", ["Sou Cliente", "Acesso Interno"], horizontal=True)
    
    if menu_publico == "Sou Cliente":
        st.markdown("<h3 style='text-align: center;'>Escritório Digital</h3>", unsafe_allow_html=True)
        st.info("Bem-vindo ao canal oficial de atendimento.")
        
        aba1, aba2 = st.tabs(["📝 NOVO PEDIDO", "🔍 CONSULTAR"])
        
        with aba1:
            with st.form("form_cliente", clear_on_submit=True):
                nome = st.text_input("Nome Completo")
                tel = st.text_input("WhatsApp")
                desc = st.text_area("Descrição do Caso")
                arquivos = st.file_uploader("Anexar Documentos", accept_multiple_files=True)
                
                if st.form_submit_button("ENVIAR SOLICITAÇÃO"):
                    if nome and desc:
                        conn = sqlite3.connect('dados_escritorio.db')
                        c = conn.cursor()
                        hoje = datetime.now().strftime("%d/%m/%Y")
                        c.execute("INSERT INTO chamados (cliente_nome, telefone, descricao, data_abertura, resposta_publica, responsavel, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                  (nome, tel, desc, hoje, "", "Sem Responsável", "Aberto"))
                        conn.commit()
                        id_gerado = c.lastrowid
                        conn.close()
                        if arquivos: salvar_arquivos(arquivos, id_gerado, "cliente")
                        st.success(f"✅ Protocolo: #{id_gerado}")
                        st.balloons()
                    else:
                        st.warning("Preencha os campos obrigatórios.")
        
        with aba2:
            prot = st.number_input("Número do Protocolo", min_value=1, step=1)
            if st.button("PESQUISAR"):
                conn = sqlite3.connect('dados_escritorio.db')
                df = pd.read_sql_query(f"SELECT * FROM chamados WHERE id = {prot}", conn)
                conn.close()
                if not df.empty:
                    status = df.iloc[0]['status']
                    resp = df.iloc[0]['resposta_publica']
                    st.metric("Status", status)
                    listar_arquivos_download(prot, "cliente")
                    st.divider()
                    if resp:
                        st.markdown(f"<div style='background-color:#00161F; padding:15px; border:1px solid {COR_DOURADO}; border-radius:5px;'>{resp}</div>", unsafe_allow_html=True)
                        listar_arquivos_download(prot, "advogado")
                    else:
                        st.info("⏳ Aguardando parecer.")
                else:
                    st.error("Protocolo não encontrado.")

    elif menu_publico == "Acesso Interno":
        st.markdown("<h3 style='text-align: center;'>Acesso Restrito</h3>", unsafe_allow_html=True)
        user = st.text_input("Login")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            conn = sqlite3.connect('dados_escritorio.db')
            c = conn.cursor()
            c.execute("SELECT nome, funcao FROM usuarios WHERE username = ? AND senha = ?", (user, senha))
            res = c.fetchone()
            conn.close()
            if res:
                st.session_state['usuario_logado'] = res[0]
                st.session_state['funcao_usuario'] = res[1]
                st.rerun()
            else:
                st.error("Acesso negado.")

# === MODO LOGADO (INTERNO) ===
else:
    # Barra de boas vindas no topo
    col_info, col_sair = st.columns([3, 1])
    with col_info:
        st.markdown(f"Olá, **{st.session_state['usuario_logado']}**")
        st.caption(st.session_state['funcao_usuario'])
    with col_sair:
        if st.button("SAIR"):
            st.session_state['usuario_logado'] = None
            st.session_state['funcao_usuario'] = None
            st.rerun()
    
    st.divider()
    
    # === SÓCIO ===
    if st.session_state['funcao_usuario'] == 'Sócio-Proprietário':
        abas = st.tabs(["📊 GERAL", "📌 TRIAGEM", "✅ VALIDAR", "👥 EQUIPE"])
        
        with abas[0]: # Geral
            conn = sqlite3.connect('dados_escritorio.db')
            df_geral = pd.read_sql_query("SELECT id, cliente_nome, status FROM chamados", conn)
            conn.close()
            st.metric("Total de Casos", len(df_geral))
            st.dataframe(df_geral, use_container_width=True, hide_index=True)

        with abas[1]: # Triagem
            conn = sqlite3.connect('dados_escritorio.db')
            df_abertos = pd.read_sql_query("SELECT * FROM chamados WHERE status='Aberto'", conn)
            df_equipe = pd.read_sql_query("SELECT nome FROM usuarios WHERE funcao != 'Sócio-Proprietário'", conn)
            conn.close()
            
            if not df_abertos.empty:
                for idx, row in df_abertos.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**#{row['id']} - {row['cliente_nome']}**")
                        st.info(row['descricao'])
                        listar_arquivos_download(row['id'], "cliente")
                        
                        opt = st.radio("Ação:", ["Delegar", "Responder"], key=f"act_{row['id']}", horizontal=True)
                        if opt == "Delegar":
                            quem = st.selectbox("Para:", df_equipe['nome'], key=f"sel_{row['id']}")
                            if st.button(f"Enviar #{row['id']}"):
                                conn = sqlite3.connect('dados_escritorio.db')
                                c = conn.cursor()
                                c.execute("UPDATE chamados SET responsavel=?, status='Em Análise' WHERE id=?", (quem, row['id']))
                                conn.commit()
                                conn.close()
                                st.success("Enviado!")
                                time.sleep(1)
                                st.rerun()
                        else:
                            resp = st.text_area("Resposta:", key=f"res_{row['id']}")
                            up = st.file_uploader("Anexo", key=f"up_{row['id']}", accept_multiple_files=True)
                            if st.button(f"Finalizar #{row['id']}"):
                                conn = sqlite3.connect('dados_escritorio.db')
                                c = conn.cursor()
                                c.execute("UPDATE chamados SET resposta_publica=?, status='Concluído', responsavel='Sócio' WHERE id=?", (resp, row['id']))
                                conn.commit()
                                conn.close()
                                if up: salvar_arquivos(up, row['id'], "advogado")
                                st.success("Feito!")
                                time.sleep(1)
                                st.rerun()
            else:
                st.success("Sem triagem.")

        with abas[2]: # Validar
            conn = sqlite3.connect('dados_escritorio.db')
            df_val = pd.read_sql_query("SELECT * FROM chamados WHERE status='Pendente Aprovação'", conn)
            conn.close()
            if not df_val.empty:
                for idx, row in df_val.iterrows():
                    with st.container(border=True):
                        st.write(f"**#{row['id']} - Resp: {row['responsavel']}**")
                        st.write(f"Minuta: {row['resposta_interna']}")
                        listar_arquivos_download(row['id'], "advogado")
                        
                        final = st.text_area("Texto Final", value=row['resposta_interna'], key=f"fin_{row['id']}")
                        if st.button(f"APROVAR #{row['id']}"):
                            conn = sqlite3.connect('dados_escritorio.db')
                            c = conn.cursor()
                            c.execute("UPDATE chamados SET resposta_publica=?, status='Concluído' WHERE id=?", (final, row['id']))
                            conn.commit()
                            conn.close()
                            st.success("Enviado!")
                            time.sleep(1)
                            st.rerun()
            else:
                st.info("Sem validações.")

        with abas[3]: # Equipe
            with st.expander("Cadastrar Novo"):
                with st.form("cad_user"):
                    n = st.text_input("Nome")
                    l = st.text_input("Login")
                    s = st.text_input("Senha", type="password")
                    t = st.selectbox("Cargo", ["Advogado", "Estagiário", "Sócio-Proprietário"])
                    if st.form_submit_button("SALVAR"):
                        conn = sqlite3.connect('dados_escritorio.db')
                        c = conn.cursor()
                        try:
                            c.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (l,s,n,t))
                            conn.commit()
                            st.success("Ok!")
                        except:
                            st.error("Login existe.")
                        conn.close()
            
            with st.expander("Manutenção"):
                conn = sqlite3.connect('dados_escritorio.db')
                users = pd.read_sql_query("SELECT username FROM usuarios", conn)
                conn.close()
                target = st.selectbox("Usuário", users['username'])
                if st.button("EXCLUIR USUÁRIO"):
                    if target == "Thiago Castro":
                        st.error("Não pode excluir o chefe!")
                    else:
                        conn = sqlite3.connect('dados_escritorio.db')
                        conn.execute("DELETE FROM usuarios WHERE username=?", (target,))
                        conn.commit()
                        conn.close()
                        st.success("Excluído!")
                        time.sleep(1)
                        st.rerun()

    # === EQUIPE ===
    else:
        st.subheader("Minhas Tarefas")
        conn = sqlite3.connect('dados_escritorio.db')
        meus = pd.read_sql_query(f"SELECT * FROM chamados WHERE responsavel='{st.session_state['usuario_logado']}' AND status != 'Concluído'", conn)
        conn.close()
        
        if not meus.empty:
            for idx, row in meus.iterrows():
                with st.container(border=True):
                    st.markdown(f"**#{row['id']} - {row['cliente_nome']}**")
                    st.info(row['descricao'])
                    listar_arquivos_download(row['id'], "cliente")
                    
                    if row['status'] == 'Pendente Aprovação':
                        st.warning("Aguardando Sócio.")
                    else:
                        txt = st.text_area("Minuta:", key=f"min_{row['id']}")
                        up = st.file_uploader("Anexo", key=f"up_{row['id']}", accept_multiple_files=True)
                        if st.button(f"ENVIAR REVISÃO #{row['id']}"):
                            conn = sqlite3.connect('dados_escritorio.db')
                            c = conn.cursor()
                            c.execute("UPDATE chamados SET resposta_interna=?, status='Pendente Aprovação' WHERE id=?", (txt, row['id']))
                            conn.commit()
                            conn.close()
                            if up: salvar_arquivos(up, row['id'], "advogado")
                            st.success("Enviado!")
                            time.sleep(1)
                            st.rerun()
        else:
            st.info("Sem tarefas.")
