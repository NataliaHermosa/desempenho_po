import streamlit as st
import pandas as pd
import gspread
import plotly.graph_objects as go 
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import os
from assistente_po import consultar_assistente_po

# ==================== CONSTANTES ====================
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit'

# ==================== CONFIGURAÇÃO ====================
st.set_page_config(
    page_title="Sistema PO - Indicadores Estratégicos",
    page_icon="📊",
    layout="wide"
)

# ==================== HELPER FUNCTIONS (Conexão) ====================
def get_google_sheet():
    """Função auxiliar para conectar ao Google Sheets"""
    # Tenta encontrar a chave correta nos secrets
    service_account_info = None
    if 'relatorio_set_out_account' in st.secrets:
        service_account_info = dict(st.secrets['relatorio_set_out_account'])
    elif 'gcp_service_account' in st.secrets:
        service_account_info = dict(st.secrets['gcp_service_account'])
        
    if not service_account_info:
        st.error("❌ Credenciais do Google Sheets não configuradas")
        return None
        
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_url(SPREADSHEET_URL)

def carregar_dados_aba(nome_aba, coluna_data=None):
    """Função genérica para carregar dados de qualquer aba"""
    try:
        spreadsheet = get_google_sheet()
        if not spreadsheet: return pd.DataFrame()
        
        aba = spreadsheet.worksheet(nome_aba)
        dados = aba.get_all_records()
        df = pd.DataFrame(dados)
        
        if not df.empty and coluna_data and coluna_data in df.columns:
            df[coluna_data] = pd.to_datetime(df[coluna_data], dayfirst=True, errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar {nome_aba}: {e}")
        return pd.DataFrame()

def salvar_registro_generico(nome_aba, linha_dados, mensagem_sucesso):
    """Função genérica para salvar registros"""
    try:
        spreadsheet = get_google_sheet()
        if not spreadsheet: return False
        
        aba = spreadsheet.worksheet(nome_aba)
        aba.append_row(linha_dados)
        
        st.success(mensagem_sucesso)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar em {nome_aba}: {e}")
        return False

# ==================== SIDEBAR COM BOTÃO DE ATUALIZAÇÃO ====================
def create_sidebar():
    st.sidebar.title("🎛️ Controle de Dados")
    
    # Botão para forçar atualização
    if st.sidebar.button("🔄 Atualizar Dados do Google Sheets", key="btn_atualizar_dados"):
        st.cache_data.clear()
        st.success("✅ Cache limpo! Os dados serão atualizados na próxima leitura.")
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Clique no botão acima para atualizar os dados diretamente do Google Sheets")

# ==================== FUNÇÕES DE FILTRO ====================
def aplicar_filtro_data(df, coluna_data, data_inicio, data_fim):
    """Aplica filtro de data em um DataFrame de forma robusta"""
    if df.empty:
        return df
    
    # Converter para datetime se ainda não for
    if df[coluna_data].dtype == 'object':
        df[coluna_data] = pd.to_datetime(df[coluna_data], dayfirst=True, errors='coerce')
    
    # Remover linhas onde a data é inválida
    df_validas = df.dropna(subset=[coluna_data]).copy()
    
    # Garantir que data_inicio e data_fim sejam datetime
    inicio = pd.to_datetime(data_inicio).normalize()
    fim = pd.to_datetime(data_fim).normalize() + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    mask = (df_validas[coluna_data] >= inicio) & (df_validas[coluna_data] <= fim)
    return df_validas.loc[mask]

def criar_filtros_sidebar():
    """Cria filtros globais na sidebar"""
    st.sidebar.header("🎛️ Filtros Globais")
    
    hoje = datetime.now()
    
    if 'data_inicio' not in st.session_state:
        st.session_state.data_inicio = hoje - timedelta(days=30)
    if 'data_fim' not in st.session_state:
        st.session_state.data_fim = hoje

    periodo = st.sidebar.selectbox(
        "Período Rápido",
        ["Personalizado", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Mês anterior", "Este trimestre"],
        key="filtro_periodo"
    )
    
    nova_data_inicio = st.session_state.data_inicio
    nova_data_fim = st.session_state.data_fim
    
    if periodo == "Últimos 7 dias":
        nova_data_inicio = hoje - timedelta(days=7)
        nova_data_fim = hoje
    elif periodo == "Últimos 30 dias":
        nova_data_inicio = hoje - timedelta(days=30)
        nova_data_fim = hoje
    elif periodo == "Este mês":
        nova_data_inicio = datetime(hoje.year, hoje.month, 1)
        nova_data_fim = hoje
    elif periodo == "Mês anterior":
        primeiro_dia_mes_anterior = datetime(hoje.year, hoje.month - 1, 1) if hoje.month > 1 else datetime(hoje.year - 1, 12, 1)
        ultimo_dia_mes_anterior = datetime(hoje.year, hoje.month, 1) - timedelta(days=1)
        nova_data_inicio = primeiro_dia_mes_anterior
        nova_data_fim = ultimo_dia_mes_anterior
    elif periodo == "Este trimestre":
        trimestre_atual = (hoje.month - 1) // 3 + 1
        mes_inicio_trimestre = (trimestre_atual - 1) * 3 + 1
        nova_data_inicio = datetime(hoje.year, mes_inicio_trimestre, 1)
        nova_data_fim = hoje
    
    if periodo != "Personalizado":
        st.session_state.data_inicio = nova_data_inicio
        st.session_state.data_fim = nova_data_fim

    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio = st.date_input("Data início", value=st.session_state.data_inicio, key="data_inicio_input")
    with col2:
        data_fim = st.date_input("Data fim", value=st.session_state.data_fim, key="data_fim_input")
    
    if data_inicio != st.session_state.data_inicio:
        st.session_state.data_inicio = data_inicio
    if data_fim != st.session_state.data_fim:
        st.session_state.data_fim = data_fim
    
    return data_inicio, data_fim

# ==================== FUNÇÕES DE CARREGAMENTO ====================
@st.cache_data(ttl=300)
def carregar_melhorias():
    return carregar_dados_aba("melhorias", "data_proposta")

@st.cache_data(ttl=300)
def carregar_cerimonias():
    return carregar_dados_aba("cerimonias_reunioes", "data")

@st.cache_data(ttl=300)
def carregar_documentos():
    return carregar_dados_aba("documentos_criterios", "data")

# ==================== FUNÇÕES DE SALVAR ====================
def salvar_melhoria(dados):
    nova_linha = [
        dados['melhoria_id'],                          
        dados['data_proposta'].strftime('%d/%m/%Y'),  
        dados['melhoria_proposta'],
        dados['descricao_detalhada'],
        dados['beneficio_esperado'],
        "SIM" if dados['melhoria_aplicada'] else "NÃO",
        dados['data_aplicacao'].strftime('%d/%m/%Y') if dados.get('data_aplicacao') else "",
        dados['status'],
        dados['impacto']
    ]
    return salvar_registro_generico("melhorias", nova_linha, "✅ Melhoria salva com sucesso!")

def salvar_cerimonia(dados):
    nova_linha = [
        dados['data'].strftime('%d/%m/%Y'),
        dados['tipo'],
        dados['nome'],
        "SIM" if dados['presente'] else "NÃO",
        dados['duracao_minutos'],
        dados['participantes'],
        dados['objetivo'],
        dados['decisoes_acoes'],
        dados['resultado']
    ]
    return salvar_registro_generico("cerimonias_reunioes", nova_linha, "✅ Cerimônia/Reunião salva com sucesso!")

def salvar_documento(dados):
    nova_linha = [
        dados['data'].strftime('%d/%m/%Y'),
        dados['tipo_documento'],
        dados['nome_documento'],
        dados['tempo_minutos'],
        "SIM" if dados['critérios_aceite'] else "NÃO",
        "SIM" if dados['template_padronizado'] else "NÃO",
        dados['status'],
        dados['observacoes']
    ]
    return salvar_registro_generico("documentos_criterios", nova_linha, "✅ Documento salvo com sucesso!")

# ==================== PÁGINA MELHORIAS ====================
def pagina_melhorias(data_inicio, data_fim):
    st.header("💡 Sistema de Melhorias")
    
    with st.expander("🔍 Filtros", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect("Status", ["Proposta", "Em análise", "Aprovada", "Implementada"], default=[], key="filtro_status_melhorias")
        with col2:
            impacto_filter = st.multiselect("Impacto", ["Alto", "Médio", "Baixo"], default=[], key="filtro_impacto_melhorias")
        with col3:
            aplicada_filter = st.selectbox("Melhoria Aplicada", ["Todos", "SIM", "NÃO"], key="filtro_aplicada_melhorias")
    
    dados_brutos = carregar_melhorias()
    
    if not dados_brutos.empty and data_inicio and data_fim and 'data_proposta' in dados_brutos.columns:
        dados = aplicar_filtro_data(dados_brutos, 'data_proposta', data_inicio, data_fim)
    else:
        dados = dados_brutos
        
    if not dados.empty:
        if status_filter: dados = dados[dados['status'].isin(status_filter)]
        if impacto_filter: dados = dados[dados['impacto'].isin(impacto_filter)]
        if aplicada_filter != "Todos":
            valor_filtro = "SIM" if aplicada_filter == "SIM" else "NÃO"
            dados = dados[dados['melhoria_aplicada'] == valor_filtro]
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Nova Melhoria", "📋 Dados"])
    
    with tab1:
        if len(dados) > 0:
            total = len(dados)
            aplicadas = len(dados[dados['melhoria_aplicada'] == 'SIM'])
            taxa = (aplicadas / total * 100) if total > 0 else 0
        
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Melhorias", total)
            col2.metric("Aplicadas", aplicadas)
            col3.metric("Taxa", f"{taxa:.1f}%")
        
            fig = px.pie(names=['Aplicadas', 'Pendentes'], values=[aplicadas, total - aplicadas], title="Taxa de Aplicação de Melhorias")
            st.plotly_chart(fig, use_container_width=True)
            
            filtros_ativos = []
            if status_filter: filtros_ativos.append(f"Status: {', '.join(status_filter)}")
            if impacto_filter: filtros_ativos.append(f"Impacto: {', '.join(impacto_filter)}")
            if aplicada_filter != "Todos": filtros_ativos.append(f"Aplicada: {aplicada_filter}")
            if filtros_ativos: st.info(f"🔍 Filtros ativos: {', '.join(filtros_ativos)}")
        else:
            if dados_brutos.empty:
                st.info("📝 Nenhuma melhoria registrada")
            else:
                st.info("🔍 Nenhuma melhoria encontrada com os filtros aplicados")

    with tab2:
        st.subheader("➕ Propor Nova Melhoria")
        with st.form(key="form_melhoria"):
            col1, col2 = st.columns(2)
            with col1:
                melhoria_id = st.text_input("ID da Melhoria", placeholder="MEL-001", key="melhoria_id")
                data_proposta = st.date_input("Data da Proposta", datetime.now(), key="data_proposta_melhoria")
                melhoria_proposta = st.text_input("Melhoria Proposta", placeholder="Descrição breve...", key="melhoria_proposta")
                status = st.selectbox("Status", ["Proposta", "Em análise", "Aprovada", "Implementada"], key="status_melhoria")
                impacto = st.selectbox("Impacto", ["Alto", "Médio", "Baixo"], key="impacto_melhoria")
            with col2:
                descricao_detalhada = st.text_area("Descrição Detalhada", placeholder="Detalhes da melhoria proposta...", key="descricao_melhoria")
                beneficio_esperado = st.text_area("Benefício Esperado", placeholder="Quais benefícios esta melhoria trará?", key="beneficio_melhoria")
                melhoria_aplicada = st.checkbox("Melhoria Aplicada?", value=False, key="aplicada_melhoria")
                data_aplicacao = None
                if melhoria_aplicada:
                    data_aplicacao = st.date_input("Data de Aplicação", datetime.now(), key="data_aplicacao_melhoria")
            
            if st.form_submit_button("💾 Salvar Melhoria", key="btn_salvar_melhoria"):
                if melhoria_id and melhoria_proposta:
                    dados_form = {
                        'melhoria_id': melhoria_id,
                        'data_proposta': data_proposta,
                        'melhoria_proposta': melhoria_proposta,
                        'descricao_detalhada': descricao_detalhada,
                        'beneficio_esperado': beneficio_esperado,
                        'melhoria_aplicada': melhoria_aplicada,
                        'data_aplicacao': data_aplicacao,
                        'status': status,
                        'impacto': impacto
                    }
                    if salvar_melhoria(dados_form):
                        st.rerun()
                else:
                    st.error("❌ Preencha pelo menos o ID e a descrição da melhoria")

    with tab3:
        st.subheader("📋 Dados Completos")
        if not dados.empty:
            st.dataframe(dados, use_container_width=True)
            csv = dados.to_csv(index=False)
            st.download_button(label="📥 Download CSV", data=csv, file_name="melhorias.csv", mime="text/csv")
        else:
            st.info("📝 Nenhum dado disponível")

# ==================== PÁGINA CERIMÔNIAS ====================
def pagina_cerimonias(data_inicio, data_fim):
    st.header("📅 Cerimônias e Reuniões")
    
    with st.expander("🔍 Filtros", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo_filter = st.multiselect("Tipo", ["Cerimônia", "Reunião"], default=[], key="filtro_tipo_cerimonias")
        with col2:
            presente_filter = st.selectbox("Presença", ["Todos", "SIM", "NÃO"], key="filtro_presenca_cerimonias")
        with col3:
            nome_filter = st.text_input("Filtrar por nome", key="filtro_nome_cerimonias")
    
    dados_brutos = carregar_cerimonias()
    
    if not dados_brutos.empty and data_inicio and data_fim:
        dados = aplicar_filtro_data(dados_brutos, 'data', data_inicio, data_fim)
    else:
        dados = dados_brutos

    if not dados.empty:
        if tipo_filter: dados = dados[dados['tipo'].isin(tipo_filter)]
        if presente_filter != "Todos": dados = dados[dados['presente'] == presente_filter]
        if nome_filter: dados = dados[dados['nome'].str.contains(nome_filter, case=False, na=False)]

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Novo Registro", "📋 Dados"])
    
    with tab1:
        if len(dados) > 0:
            total_registros = len(dados)
            presencas = len(dados[dados['presente'] == 'SIM'])
            taxa_presenca = (presencas / total_registros * 100) if total_registros > 0 else 0
            total_minutos = dados['duracao_minutos'].sum()
            horas_totais = total_minutos / 60
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Registros", total_registros)
            col2.metric("Presenças", presencas)
            col3.metric("Taxa Presença", f"{taxa_presenca:.1f}%")
            col4.metric("Horas em Reunião", f"{horas_totais:.1f}h")
            
            col1, col2 = st.columns(2)
            with col1:
                tipo_count = dados['tipo'].value_counts()
                fig_tipo = px.pie(names=tipo_count.index, values=tipo_count.values, title="Distribuição por Tipo")
                st.plotly_chart(fig_tipo, use_container_width=True)
            with col2:
                tempo_por_tipo = dados.groupby('tipo')['duracao_minutos'].sum().reset_index()
                fig_tempo = px.bar(tempo_por_tipo, x='tipo', y='duracao_minutos', title="Tempo Total por Tipo (minutos)")
                st.plotly_chart(fig_tempo, use_container_width=True)
        else:
            st.info("Nenhuma cerimônia ou reunião encontrada no período selecionado.")

    with tab2:
        with st.form(key="form_cerimonia"):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("Data", datetime.now(), key="data_cerimonia")
                tipo = st.selectbox("Tipo", ["Cerimônia", "Reunião"], key="tipo_cerimonia")
                nome = st.text_input("Nome", placeholder="Daily, Planning, Review...", key="nome_cerimonia")
                presente = st.checkbox("Presente?", value=True, key="presente_cerimonia")
                duracao = st.number_input("Duração (minutos)", min_value=1, value=30, key="duracao_cerimonia")
            with col2:
                participantes = st.text_input("Participantes", placeholder="PO, Devs, QA...", key="participantes_cerimonia")
                objetivo = st.text_area("Objetivo", key="objetivo_cerimonia")
                decisoes = st.text_area("Decisões/Ações", key="decisoes_cerimonia")
                resultado = st.text_area("Resultado", key="resultado_cerimonia")
            
            if st.form_submit_button("💾 Salvar Cerimônia/Reunião", key="btn_salvar_cerimonia"):
                dados_form = {
                    'data': data,
                    'tipo': tipo,
                    'nome': nome,
                    'presente': presente,
                    'duracao_minutos': duracao,
                    'participantes': participantes,
                    'objetivo': objetivo,
                    'decisoes_acoes': decisoes,
                    'resultado': resultado
                }
                if salvar_cerimonia(dados_form):
                    st.rerun()
    
    with tab3:
        if not dados.empty:
            st.dataframe(dados, use_container_width=True)
        else:
            st.info("Nenhum dado disponível")

# ==================== PÁGINA DOCUMENTOS ENTREGUES ====================
def pagina_documentos(data_inicio, data_fim):
    st.header("📋 Documentos Elaborados e Entregues")

    with st.expander("🔍 Filtros", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            tipo_doc_filter = st.multiselect("Tipo de Documento", ["User Story", "Especificação", "Layout", "Processo", "Relatório", "Critérios de Aceite"], default=[], key="filtro_tipo_documentos")
        with col2:
            status_doc_filter = st.multiselect("Status", ["Rascunho", "Revisão", "Aprovado", "Entregue"], default=[], key="filtro_status_documentos")
    
    dados_brutos = carregar_documentos()

    if not dados_brutos.empty and data_inicio and data_fim:
        dados = aplicar_filtro_data(dados_brutos, 'data', data_inicio, data_fim)
    else:
        dados = dados_brutos
        
    if not dados.empty:
        if tipo_doc_filter: dados = dados[dados['tipo_documento'].isin(tipo_doc_filter)]
        if status_doc_filter: dados = dados[dados['status'].isin(status_doc_filter)]
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Novo Documento", "📋 Dados"])
    
    with tab1:
        if len(dados) > 0:
            total_documentos = len(dados)
            docs_criterios = len(dados[dados['critérios_aceite'] == 'SIM'])
            docs_templates = len(dados[dados['template_padronizado'] == 'SIM'])
            tempo_total = dados['tempo_minutos'].sum()
            tempo_medio = tempo_total / total_documentos if total_documentos > 0 else 0
            
            taxa_criterios = (docs_criterios / total_documentos * 100) if total_documentos > 0 else 0
            taxa_templates = (docs_templates / total_documentos * 100) if total_documentos > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Documentos", total_documentos)
            col2.metric("Taxa Critérios", f"{taxa_criterios:.1f}%")
            col3.metric("Taxa Templates", f"{taxa_templates:.1f}%")
            col4.metric("Tempo Médio", f"{tempo_medio:.0f} min")
            
            col1, col2 = st.columns(2)
            with col1:
                tipo_count = dados['tipo_documento'].value_counts()
                fig_tipo = px.pie(names=tipo_count.index, values=tipo_count.values, title="Distribuição por Tipo de Documento")
                st.plotly_chart(fig_tipo, use_container_width=True)
            with col2:
                tempo_por_tipo = dados.groupby('tipo_documento')['tempo_minutos'].mean().reset_index()
                fig_tempo = px.bar(tempo_por_tipo, x='tipo_documento', y='tempo_minutos', title="Tempo Médio por Tipo (minutos)")
                st.plotly_chart(fig_tempo, use_container_width=True)
            
            st.subheader("⏱️ Análise de Produtividade")
            horas_totais = tempo_total / 60
            dias_trabalho = len(dados['data'].unique())
            horas_por_dia = horas_totais / dias_trabalho if dias_trabalho > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Horas Totais", f"{horas_totais:.1f}h")
            col2.metric("Dias com Documentação", dias_trabalho)
            col3.metric("Média Diária", f"{horas_por_dia:.1f}h/dia")
        else:
            st.info("Nenhum documento registrado no período/filtros selecionados")
        
    with tab2:
        with st.form(key="form_documento"):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("Data de Entrega", datetime.now(), key="data_documento")
                tipo_documento = st.selectbox("Tipo de Documento", ["User Story", "Especificação", "Layout", "Processo", "Relatório", "Critérios de Aceite"], key="tipo_documento")
                nome_documento = st.text_input("Nome do Documento", placeholder="US-001 - Login, Fluxo de Pagamento...", key="nome_documento")
                tempo_minutos = st.number_input("Tempo Gasto (minutos)", min_value=1, value=60, key="tempo_documento")
                status = st.selectbox("Status", ["Rascunho", "Revisão", "Aprovado", "Entregue"], key="status_documento")
            with col2:
                criterios_aceite = st.checkbox("Possui critérios de aceite claros?", value=True, key="criterios_documento")
                template_padronizado = st.checkbox("Usa template padronizado?", value=True, key="template_documento")
                observacoes = st.text_area("Observações", placeholder="Dificuldades, feedbacks, etc...", key="observacoes_documento")
            
            if st.form_submit_button("💾 Salvar Documento", key="btn_salvar_documento"):
                dados_form = {
                    'data': data,
                    'tipo_documento': tipo_documento,
                    'nome_documento': nome_documento,
                    'tempo_minutos': tempo_minutos,
                    'critérios_aceite': criterios_aceite,
                    'template_padronizado': template_padronizado,
                    'status': status,
                    'observacoes': observacoes
                }
                if salvar_documento(dados_form):
                    st.rerun()
    
    with tab3:
        if len(dados) > 0:
            st.dataframe(dados, use_container_width=True)
        else:
            st.info("Nenhum documento disponível")

# ==================== FUNÇÂO IA =========================
def pagina_ia_assistente(data_inicio, data_fim):
    st.header("🤖 Assistente de IA - Análise de PO")
    
    dados_disponiveis = {
        'melhorias': carregar_melhorias(),
        'cerimonias': carregar_cerimonias(),
        'documentos': carregar_documentos()
    }
    
    for categoria, df in dados_disponiveis.items():
        if not df.empty:
            coluna_data = None
            if categoria == 'melhorias' and 'data_proposta' in df.columns:
                coluna_data = 'data_proposta'
            elif categoria == 'cerimonias' and 'data' in df.columns:
                coluna_data = 'data'
            elif categoria == 'documentos' and 'data' in df.columns:
                coluna_data = 'data'
            
            if coluna_data and data_inicio and data_fim:
                dados_disponiveis[categoria] = aplicar_filtro_data(df, coluna_data, data_inicio, data_fim)
    
    st.markdown("""
    ### 💬 Faça perguntas sobre seus dados de Product Ownership
    **Exemplos de perguntas:**
    - "Como está minha performance nas cerimônias ágeis?"
    - "Qual a eficiência na documentação das user stories?"
    - "Quais melhorias posso implementar no processo de priorização?"
    - "Analise minha produtividade nos últimos 30 dias"
    """)
    
    pergunta = st.text_area("Sua pergunta:", placeholder="Ex: Analise minha eficiência na documentação e sugira melhorias...", height=100, key="pergunta_ia")
    
    if st.button("🔍 Analisar com IA", type="primary", key="btn_analisar_ia"):
        if pergunta.strip():
            with st.spinner("🤖 Analisando dados e gerando insights..."):
                try:
                    gemini_key = st.secrets['gemini']['api_key']
                except:
                    gemini_key = None
                    st.warning("⚠️ Chave Gemini não encontrada nos secrets")
                
                resposta = consultar_assistente_po(pergunta=pergunta, dados_disponiveis=dados_disponiveis, gemini_key=gemini_key)
                
            st.markdown("---")
            st.markdown("### 📊 Resposta da Análise")
            st.markdown(resposta)
        else:
            st.warning("⚠️ Por favor, digite uma pergunta para análise.")

    st.markdown("---")
    st.subheader("📈 Dados Disponíveis para Análise")
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Melhorias", len(dados_disponiveis['melhorias']))
    with col2: st.metric("Cerimônias", len(dados_disponiveis['cerimonias']))
    with col3: st.metric("Documentos", len(dados_disponiveis['documentos']))

def obter_data_mais_antiga():
    """Verifica em todos os dataframes qual é a data mais antiga registrada"""
    datas_minimas = []
    
    df = carregar_melhorias()
    if not df.empty and 'data_proposta' in df.columns:
        min_val = df['data_proposta'].min()
        if pd.notnull(min_val): datas_minimas.append(min_val)
            
    df = carregar_cerimonias()
    if not df.empty and 'data' in df.columns:
        min_val = df['data'].min()
        if pd.notnull(min_val): datas_minimas.append(min_val)
            
    df = carregar_documentos()
    if not df.empty and 'data' in df.columns:
        min_val = df['data'].min()
        if pd.notnull(min_val): datas_minimas.append(min_val)
            
    if datas_minimas:
        return min(datas_minimas)
    return None

# ==================== MENU PRINCIPAL ====================
def main():
    if 'data_inicio' not in st.session_state:
        st.session_state.data_inicio = datetime.now() - timedelta(days=30)
    if 'data_fim' not in st.session_state:
        st.session_state.data_fim = datetime.now()
    
    create_sidebar()
    
    st.title("📊 Sistema PO - Indicadores Estratégicos")

    data_inicio, data_fim = criar_filtros_sidebar()
           
    st.sidebar.info(f"**Período selecionado:**\n{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    
    data_antiga = obter_data_mais_antiga()
    if data_antiga:
        st.sidebar.success(f"📅 **Registros a partir de:**\n{data_antiga.strftime('%d/%m/%Y')}")

    menu = st.sidebar.selectbox(
        "Navegação",
        ["💡 Melhorias", "📅 Cerimônias", "📋 Documentos", "🤖 Assistente IA"],
        key="menu_principal"
    )
    
    if menu == "💡 Melhorias":
        pagina_melhorias(data_inicio, data_fim)
    elif menu == "📅 Cerimônias":
        pagina_cerimonias(data_inicio, data_fim)
    elif menu == "📋 Documentos":
        pagina_documentos(data_inicio, data_fim)
    elif menu == "🤖 Assistente IA":
        pagina_ia_assistente(data_inicio, data_fim)

if __name__ == "__main__":
    main()