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

# Cores
COR_DOURADO = "#Cea065"
COR_FUNDO = "#00202f"
COR_SIDEBAR = "#00202f"

st.set_page_config(
    page_title=TITULO_ABA, 
    page_icon="⚖️", 
    layout="wide", 
    initial_sidebar_state="auto"
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
        else:
            st.caption(f"Sem anexos de {quem_enviou}.")

# --- 3. CSS "FLEXBOX PURO" (CENTRALIZAÇÃO RESPONSIVA) ---
def configurar_estilo_visual():
    st.markdown(f"""
        <style>
        :root {{ --primary-color: {COR_DOURADO}; }}
        header {{ visibility: hidden; }}
        
        /* Fundo Geral */
        [data-testid="stAppViewContainer"] {{ background-color: {COR_FUNDO}; color: white; }}
        [data-testid="stSidebar"] {{ background-color: {COR_SIDEBAR}; border-right: 1px solid {COR_DOURADO}; }}
        
        /* Textos */
        h1, h2, h3 {{ color: {COR_DOURADO} !important; text-align: center; }}
        p, label, .stMarkdown {{ color: white !important; }}
        
        /* --- CENTRALIZAÇÃO DOS ELEMENTOS --- */
        
        /* 1. Centraliza a Logo */
        [data-testid="stImage"] {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin-bottom: 20px;
        }}
        
        /* 2. Centraliza o Container do Botão (A caixa invisível) */
        .stButton {{
            display: flex;
            justify-content: center;
            width: 100%;
        }}
        
        /* 3. Estilo do Botão Primário (Dourado) */
        button[kind="primary"] {{
            background-color: {COR_DOURADO} !important;
            border: none !important;
            color: black !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            font-size: 18px !important;
            
            /* LARGURA RESPONSIVA (O Segredo) */
            width: 80% !important;      /* Ocupa 80% da tela no celular */
            max-width: 350px !important; /* Mas não passa de 350px no PC */
            height: 65px !important;     /* Altura fixa */
            
            /* Centralização interna do texto */
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin: 0 auto !important;
        }}
        
        button[kind="primary"] p {{
            color: black !important; font-size: 18px !important; margin: 0 !important;
        }}
        
        /* 4. Estilo do Botão Secundário (Voltar) */
        button[kind="secondary"] {{
            background-color: transparent !important;
            border: 2px solid {COR_DOURADO} !important;
            color: {COR_DOURADO} !important;
            
            /* Mesma regra de largura */
            width: 80% !important;
            max-width: 350px !important;
            
            padding: 10px !important;
            border-radius: 8px !important;
            margin-top: 15px !important;
        }}
        button[kind="secondary"] p {{ color: {COR_DOURADO} !important; font-weight: bold !important; }}
        
        /* Hover */
        button[kind="primary"]:hover {{ background-color: #b38b52 !important; }}
        button[kind="secondary"]:hover {{ border-color: white !important; color: white !important; }}

        /* --- INPUTS --- */
        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div {{
            background-color: white !important;
            border: 2px solid {COR_DOURADO} !important;
            border-radius: 8px !important;
        }}
        input {{ color: black !important; }}
        button[aria-label="Password visibility"] {{ color: {COR_FUNDO} !important; }}
        
        /* Resto */
        .stTabs [data-baseweb="tab-highlight"] {{ background-color: {COR_DOURADO} !important; }}
        .block-container {{ padding-top: 3rem; }}
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

# --- 5. VARIÁVEIS E SIDEBAR ---
if 'usuario_logado' not in st.session_state:
    st.session_state['usuario_logado'] = None
if 'funcao_usuario' not in st.session_state:
    st.session_state['funcao_usuario'] = None
if 'tipo_acesso' not in st.session_state:
    st.session_state['tipo_acesso'] = None

def sidebar_logada():
    with st.sidebar:
        try:
            logo = Image.open("logo.png")
            st.image(logo, use_container_width=True)
        except:
            st.markdown(f"## {NOME_ESCRITORIO}")
        
        st.write("")
        if st.session_state['usuario_logado']:
            cargo = st.session_state['funcao_usuario']
            st.markdown(f"""
                <div style="padding: 15px; border: 1px solid {COR_DOURADO}; border-radius: 5px; text-align: center; margin-bottom: 20px; background-color: #00161F;">
                    <small style="color: #ccc;">Logado como</small><br>
                    <strong style="color: white; font-size: 16px;">{st.session_state['usuario_logado']}</strong><br>
                    <span style="color: {COR_DOURADO}; font-size: 12px; text-transform: uppercase;">{cargo}</span>
                </div>
            """, unsafe_allow_html=True)
            if st.button("SAIR / LOGOUT"):
                st.session_state['usuario_logado'] = None
                st.session_state['funcao_usuario'] = None
                st.session_state['tipo_acesso'] = None
                st.rerun()

# --- 6. LÓGICA DO SISTEMA ---

# Header
try:
    logo = Image.open("logo.png")
    st.image(logo, width=240)
except:
    st.title(NOME_ESCRITORIO)
st.write("")

# === SE NÃO ESTIVER LOGADO ===
if st.session_state['usuario_logado'] is None:
    
    # TELA 0: PÁGINA INICIAL (LANDING PAGE)
    if st.session_state['tipo_acesso'] is None:
        
        # MENSAGEM DE BOAS VINDAS
        st.markdown(f"<h1 style='margin-bottom: 0px;'>Seja bem-vindo(a)</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: white; margin-top: 5px; margin-bottom: 40px; font-weight: normal; font-size: 18px;'>Selecione seu perfil de acesso</h3>", unsafe_allow_html=True)
        
        # BOTÕES (Sem colunas, apenas empilhados e centralizados pelo CSS)
        
        if st.button("Sou Cliente", type="primary"):
            st.session_state['tipo_acesso'] = 'cliente'
            st.rerun()
        
        # Espaço vertical manual para garantir separação
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        if st.button("Sou Advogado", type="primary"):
            st.session_state['tipo_acesso'] = 'interno'
            st.rerun()

    # TELA 1: ÁREA DO CLIENTE
    elif st.session_state['tipo_acesso'] == 'cliente':
        # Botão voltar
        if st.button("⬅ VOLTAR", type="secondary"):
            st.session_state['tipo_acesso'] = None
            st.rerun()
            
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
                        st.warning("Preencha os campos.")
        
        with aba2:
            prot = st.number_input("Número do Protocolo", min_value=1, step=1)
            if st.button("PESQUISAR", type="primary"):
                conn = sqlite3.connect('dados_escritorio.db')
                df = pd.read_sql_query(f"SELECT * FROM chamados WHERE id = {prot}", conn)
                conn.close()
                if not df.empty:
                    status = df.iloc[0]['status']
                    resp = df.iloc[0]['resposta_publica']
                    st.markdown(f"**Status:** {status}")
                    listar_arquivos_download(prot, "cliente")
                    st.divider()
                    if resp:
                        st.markdown(f"<div style='background-color:#00161F; padding:15px; border:1px solid {COR_DOURADO}; border-radius:5px;'>{resp}</div>", unsafe_allow_html=True)
                        listar_arquivos_download(prot, "advogado")
                    else:
                        st.info("⏳ Aguardando parecer.")
                else:
                    st.error("Não encontrado.")

    # TELA 2: LOGIN DA EQUIPE
    elif st.session_state['tipo_acesso'] == 'interno':
        if st.button("⬅ VOLTAR", type="secondary"):
            st.session_state['tipo_acesso'] = None
            st.rerun()

        st.markdown("<h4 style='text-align: center; color: white; margin-top: 20px;'>Login Corporativo</h4>", unsafe_allow_html=True)
        
        # Centralizando Login com CSS (as colunas do streamlit as vezes atrapalham o width:100%)
        user = st.text_input("Login")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR", type="primary"):
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

# === MODO LOGADO ===
else:
    sidebar_logada()
    cargo_atual = st.session_state['funcao_usuario']
    
    if cargo_atual == 'Sócio-Proprietário':
        st.title("Painel do Sócio")
        abas_admin = st.tabs(["📊 Visão", "📌 Triagem", "✅ Validar", "👥 Equipe"])
        
        with abas_admin[0]: # Visão
            conn = sqlite3.connect('dados_escritorio.db')
            df_geral = pd.read_sql_query("SELECT id, cliente_nome, status, responsavel FROM chamados", conn)
            conn.close()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", len(df_geral))
            c2.metric("Abertos", len(df_geral[df_geral['status']=='Aberto']))
            c3.metric("Análise", len(df_geral[df_geral['status']=='Em Análise']))
            c4.metric("Final", len(df_geral[df_geral['status']=='Concluído']))
            st.dataframe(df_geral, use_container_width=True, hide_index=True)

        with abas_admin[1]: # Triagem
            conn = sqlite3.connect('dados_escritorio.db')
            df_abertos = pd.read_sql_query("SELECT id, cliente_nome, descricao FROM chamados WHERE status='Aberto'", conn)
            df_equipe = pd.read_sql_query("SELECT nome FROM usuarios WHERE funcao != 'Sócio-Proprietário'", conn)
            lista_equipe = df_equipe['nome'].tolist()
            conn.close()
            
            if not df_abertos.empty:
                for index, row in df_abertos.iterrows():
                    with st.expander(f"Caso #{row['id']} - {row['cliente_nome']}", expanded=True):
                        st.info(row['descricao'])
                        listar_arquivos_download(row['id'], "cliente")
                        st.markdown("---")
                        col_acao, col_detalhe = st.columns([1, 2])
                        opcao = col_acao.radio(f"Ação #{row['id']}:", ["Delegar", "Responder Agora"], key=f"rd_{row['id']}")
                        
                        if opcao == "Delegar":
                            if not lista_equipe:
                                st.warning("Cadastre sua equipe.")
                            else:
                                func_sel = col_detalhe.selectbox("Para:", lista_equipe, key=f"sel_{row['id']}")
                                if col_detalhe.button(f"Confirmar #{row['id']}"):
                                    conn = sqlite3.connect('dados_escritorio.db')
                                    c = conn.cursor()
                                    c.execute("UPDATE chamados SET responsavel = ?, status = 'Em Análise' WHERE id = ?", (func_sel, row['id']))
                                    conn.commit()
                                    conn.close()
                                    st.success("Delegado!")
                                    time.sleep(1)
                                    st.rerun()
                        else:
                            resp_direta = col_detalhe.text_area("Resposta:", key=f"txt_{row['id']}")
                            arq_socio = col_detalhe.file_uploader("Anexar", key=f"up_{row['id']}", accept_multiple_files=True)
                            if col_detalhe.button(f"Finalizar #{row['id']}"):
                                conn = sqlite3.connect('dados_escritorio.db')
                                c = conn.cursor()
                                c.execute("UPDATE chamados SET resposta_publica = ?, status = 'Concluído', responsavel = 'Sócio-Proprietário' WHERE id = ?", (resp_direta, row['id']))
                                conn.commit()
                                conn.close()
                                if arq_socio: salvar_arquivos(arq_socio, row['id'], "advogado")
                                st.success("Respondido!")
                                time.sleep(1)
                                st.rerun()
            else:
                st.success("Fila zerada.")

        with abas_admin[2]: # Validar
            conn = sqlite3.connect('dados_escritorio.db')
            df_rev = pd.read_sql_query("SELECT * FROM chamados WHERE status='Pendente Aprovação'", conn)
            conn.close()
            if not df_rev.empty:
                for index, row in df_rev.iterrows():
                    with st.expander(f"Caso #{row['id']} - Resp: {row['responsavel']}", expanded=True):
                        st.write(f"**Descrição:** {row['descricao']}")
                        listar_arquivos_download(row['id'], "cliente")
                        st.info(f"**Minuta:**\n{row['resposta_interna']}")
                        listar_arquivos_download(row['id'], "advogado")
                        resposta_final = st.text_area("Texto Final", value=row['resposta_interna'], key=f"edit_{row['id']}")
                        if st.button(f"APROVAR #{row['id']}"):
                            conn = sqlite3.connect('dados_escritorio.db')
                            c = conn.cursor()
                            c.execute("UPDATE chamados SET resposta_publica = ?, status = 'Concluído' WHERE id = ?", (resposta_final, row['id']))
                            conn.commit()
                            conn.close()
                            st.success("Enviado!")
                            time.sleep(1)
                            st.rerun()
            else:
                st.info("Nada para validar.")

        with abas_admin[3]: # Equipe
            col_cad, col_manut = st.columns(2)
            with col_cad:
                st.subheader("Novo Membro")
                with st.form("novo_user"):
                    u_nome = st.text_input("Nome")
                    u_login = st.text_input("Login")
                    u_senha = st.text_input("Senha", type="password")
                    u_tipo = st.selectbox("Cargo", ["Advogado", "Estagiário", "Sócio-Proprietário"])
                    if st.form_submit_button("CADASTRAR"):
                        conn = sqlite3.connect('dados_escritorio.db')
                        c = conn.cursor()
                        try:
                            c.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", (u_login, u_senha, u_nome, u_tipo))
                            conn.commit()
                            st.success("Cadastrado!")
                        except:
                            st.error("Login já existe.")
                        conn.close()
            
            with col_manut:
                st.subheader("Manutenção")
                conn = sqlite3.connect('dados_escritorio.db')
                df_users = pd.read_sql_query("SELECT username, nome, funcao FROM usuarios", conn)
                conn.close()
                
                with st.expander("🔑 Alterar Senha"):
                    user_reset = st.selectbox("Usuário", df_users['username'])
                    pass_reset = st.text_input("Nova Senha", type="password")
                    if st.button("ATUALIZAR"):
                        conn = sqlite3.connect('dados_escritorio.db')
                        c = conn.cursor()
                        c.execute("UPDATE usuarios SET senha = ? WHERE username = ?", (pass_reset, user_reset))
                        conn.commit()
                        conn.close()
                        st.success("Senha alterada!")

                st.write("")
                with st.expander("🗑️ Excluir"):
                    df_delete = df_users[df_users['funcao'] != 'Sócio-Proprietário']
                    if not df_delete.empty:
                        user_delete = st.selectbox("Quem excluir?", df_delete['username'])
                        if st.button("CONFIRMAR EXCLUSÃO", type="primary"):
                            conn = sqlite3.connect('dados_escritorio.db')
                            c = conn.cursor()
                            c.execute("DELETE FROM usuarios WHERE username = ?", (user_delete,))
                            conn.commit()
                            conn.close()
                            st.success("Removido!")
                            time.sleep(1)
                            st.rerun()
            st.write("---")
            st.dataframe(df_users[['nome', 'username', 'funcao']], hide_index=True, use_container_width=True)

    # === PAINEL STAFF ===
    else:
        st.title(f"Minhas Tarefas | {st.session_state['usuario_logado']}")
        conn = sqlite3.connect('dados_escritorio.db')
        meus_casos = pd.read_sql_query(f"SELECT * FROM chamados WHERE responsavel = '{st.session_state['usuario_logado']}' AND status != 'Concluído'", conn)
        conn.close()
        
        if not meus_casos.empty:
            for index, row in meus_casos.iterrows():
                with st.container(border=True):
                    st.markdown(f"**Caso #{row['id']} - {row['cliente_nome']}**")
                    st.info(row['descricao'])
                    listar_arquivos_download(row['id'], "cliente")
                    
                    if row['status'] == 'Pendente Aprovação':
                        st.warning("⏳ Aguardando validação do Sócio.")
                    else:
                        resposta = st.text_area("Elaborar Resposta:", key=f"staff_{row['id']}")
                        arq_staff = st.file_uploader("Anexar", key=f"up_staff_{row['id']}", accept_multiple_files=True)
                        
                        if st.button(f"ENVIAR PARA VALIDAÇÃO #{row['id']}"):
                            conn = sqlite3.connect('dados_escritorio.db')
                            c = conn.cursor()
                            c.execute("UPDATE chamados SET resposta_interna = ?, status = 'Pendente Aprovação' WHERE id = ?", (resposta, row['id']))
                            conn.commit()
                            conn.close()
                            if arq_staff: salvar_arquivos(arq_staff, row['id'], "advogado")
                            st.success("Enviado!")
                            time.sleep(1)
                            st.rerun()
        else:
            st.success("Sua fila de tarefas está vazia.")
