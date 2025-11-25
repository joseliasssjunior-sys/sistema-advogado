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
COR_SIDEBAR = "#00202f"

st.set_page_config(
    page_title=TITULO_ABA, 
    page_icon="⚖️", 
    layout="wide", 
    initial_sidebar_state="expanded"
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

# --- 3. CSS ESTILIZADO ---
def configurar_estilo_visual():
    st.markdown(f"""
        <style>
        :root {{ --primary-color: {COR_DOURADO}; }}
        header {{ visibility: hidden; }}
        [data-testid="stAppViewContainer"] {{ background-color: {COR_FUNDO}; color: white; }}
        [data-testid="stSidebar"] {{ background-color: {COR_SIDEBAR}; border-right: 1px solid {COR_DOURADO}; }}
        h1, h2, h3 {{ color: {COR_DOURADO} !important; font-family: 'Helvetica', sans-serif; }}
        
        /* Botões */
        [data-testid="stFormSubmitButton"] > button,
        [data-testid="baseButton-primary"] {{
            background-color: {COR_DOURADO} !important;
            color: black !important;
            border: none !important;
            font-weight: bold !important;
        }}
        [data-testid="stFormSubmitButton"] > button:hover,
        [data-testid="baseButton-primary"]:hover {{ background-color: #b38b52 !important; }}
        
        /* Inputs e Selects */
        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div {{
            background-color: #00161F !important;
            border-color: {COR_DOURADO} !important;
            color: white !important;
            border-radius: 5px !important;
        }}
        input {{ color: white !important; }}
        button[aria-label="Password visibility"] {{ color: {COR_DOURADO} !important; }}
        
        /* Tabs e Radios */
        .stTabs [data-baseweb="tab-highlight"] {{ background-color: {COR_DOURADO} !important; }}
        div[role="radiogroup"] > label > div:first-child {{ background-color: {COR_DOURADO} !important; border-color: {COR_DOURADO} !important; }}
        [data-testid="stSidebar"] label {{ color: white !important; font-size: 16px; }}
        .block-container {{ padding-top: 2rem; }}
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

# --- 5. SIDEBAR ---
if 'usuario_logado' not in st.session_state:
    st.session_state['usuario_logado'] = None
if 'funcao_usuario' not in st.session_state:
    st.session_state['funcao_usuario'] = None

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
                st.rerun()

# --- 6. LÓGICA DO SISTEMA ---
if st.session_state['usuario_logado'] is None:
    # === ÁREA PÚBLICA ===
    sidebar_logada()
    menu_publico = st.sidebar.radio("Navegação", ["Sou Cliente", "Acesso Interno"])
    
    if menu_publico == "Sou Cliente":
        col1, col2 = st.columns([2, 1])
        with col1:
            st.title("Escritório Digital")
            st.markdown("Canal oficial de comunicação para clientes.")
        st.divider()
        
        aba1, aba2 = st.tabs(["📝 NOVO ATENDIMENTO", "🔍 CONSULTAR MEU PROCESSO"])
        
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
                        if arquivos:
                            salvar_arquivos(arquivos, id_gerado, "cliente")
                        st.success(f"Protocolo gerado: #{id_gerado}")
                        st.balloons()
        
        with aba2:
            prot = st.number_input("Digite o Protocolo", min_value=1, step=1)
            if st.button("PESQUISAR"):
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
                        st.markdown(f"<div style='background-color:#00161F; padding:15px; border-left:3px solid {COR_DOURADO}'>{resp}</div>", unsafe_allow_html=True)
                        listar_arquivos_download(prot, "advogado")
                    else:
                        st.warning("Aguardando parecer final.")
                else:
                    st.error("Não encontrado.")

    elif menu_publico == "Acesso Interno":
        st.title("🔒 Acesso Restrito")
        col_login, _ = st.columns([1,2])
        with col_login:
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
                    st.error("Login ou senha incorretos.")

else:
    # === ÁREA LOGADA ===
    sidebar_logada()
    cargo_atual = st.session_state['funcao_usuario']
    
    # === PAINEL DO SÓCIO-PROPRIETÁRIO ===
    if cargo_atual == 'Sócio-Proprietário':
        st.title("Painel do Sócio")
        
        abas_admin = st.tabs(["📊 Visão Geral", "📌 Triagem", "✅ Validação", "👥 Equipe & Senhas"])
        
        with abas_admin[0]:
            st.subheader("Monitoramento Global")
            conn = sqlite3.connect('dados_escritorio.db')
            df_geral = pd.read_sql_query("SELECT id, cliente_nome, status, responsavel FROM chamados", conn)
            conn.close()
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", len(df_geral))
            c2.metric("Abertos", len(df_geral[df_geral['status']=='Aberto']))
            c3.metric("Análise", len(df_geral[df_geral['status']=='Em Análise']))
            c4.metric("Finalizados", len(df_geral[df_geral['status']=='Concluído']))
            st.dataframe(df_geral, use_container_width=True, hide_index=True)

        with abas_admin[1]:
            st.subheader("Triagem de Casos")
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
                                st.warning("Cadastre sua equipe primeiro.")
                            else:
                                func_sel = col_detalhe.selectbox("Delegar para:", lista_equipe, key=f"sel_{row['id']}")
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

        with abas_admin[2]:
            st.subheader("Validar Trabalho")
            conn = sqlite3.connect('dados_escritorio.db')
            df_rev = pd.read_sql_query("SELECT * FROM chamados WHERE status='Pendente Aprovação'", conn)
            conn.close()
            if not df_rev.empty:
                for index, row in df_rev.iterrows():
                    with st.expander(f"Caso #{row['id']} - Responsável: {row['responsavel']}", expanded=True):
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

        # 4. GESTÃO DE PESSOAS (COM EXCLUSÃO)
        with abas_admin[3]:
            col_cad, col_manut = st.columns(2)
            
            with col_cad:
                st.subheader("Novo Membro")
                with st.form("novo_user"):
                    u_nome = st.text_input("Nome Completo")
                    u_login = st.text_input("Login")
                    u_senha = st.text_input("Senha Provisória", type="password")
                    u_tipo = st.selectbox("Cargo", ["Advogado", "Estagiário", "Sócio-Proprietário"])
                    if st.form_submit_button("CADASTRAR"):
                        conn = sqlite3.connect('dados_escritorio.db')
                        c = conn.cursor()
                        try:
                            c.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", (u_login, u_senha, u_nome, u_tipo))
                            conn.commit()
                            st.success(f"{u_nome} cadastrado!")
                        except:
                            st.error("Login já existe.")
                        conn.close()
            
            with col_manut:
                st.subheader("⚙️ Manutenção")
                conn = sqlite3.connect('dados_escritorio.db')
                df_users = pd.read_sql_query("SELECT username, nome, funcao FROM usuarios", conn)
                conn.close()
                
                # RESET DE SENHA
                with st.expander("🔑 Alterar Senha"):
                    user_reset = st.selectbox("Usuário", df_users['username'], key="sel_reset")
                    pass_reset = st.text_input("Nova Senha", type="password", key="pass_reset")
                    if st.button("ATUALIZAR SENHA"):
                        conn = sqlite3.connect('dados_escritorio.db')
                        c = conn.cursor()
                        c.execute("UPDATE usuarios SET senha = ? WHERE username = ?", (pass_reset, user_reset))
                        conn.commit()
                        conn.close()
                        st.success("Senha alterada!")

                # EXCLUIR MEMBRO
                st.write("")
                with st.expander("🗑️ Excluir Membro"):
                    # Filtra para não mostrar o próprio Sócio (Segurança)
                    df_delete = df_users[df_users['funcao'] != 'Sócio-Proprietário']
                    
                    if not df_delete.empty:
                        user_delete = st.selectbox("Quem excluir?", df_delete['username'], key="sel_del")
                        if st.button("CONFIRMAR EXCLUSÃO", type="primary"):
                            conn = sqlite3.connect('dados_escritorio.db')
                            c = conn.cursor()
                            c.execute("DELETE FROM usuarios WHERE username = ?", (user_delete,))
                            conn.commit()
                            conn.close()
                            st.success(f"{user_delete} removido!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.info("Nenhum membro passível de exclusão.")

            st.write("---")
            st.write("Equipe Ativa:")
            st.dataframe(df_users[['nome', 'username', 'funcao']], hide_index=True, use_container_width=True)

    # === PAINEL DE ADVOGADOS E ESTAGIÁRIOS ===
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