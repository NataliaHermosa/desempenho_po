import streamlit as st
import pandas as pd
import gspread
import plotly.graph_objects as go 
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import os
from assistente_po import consultar_assistente_po


# Configuração da página
st.set_page_config(
    page_title="Sistema PO - Indicadores Estratégicos",
    page_icon="📊",
    layout="wide"
)

# ==================== SIDEBAR COM BOTÃO DE ATUALIZAÇÃO ====================
def create_sidebar():
    st.sidebar.title("🎛️ Controle de Dados")
    
    # Botão para forçar atualização - COM KEY ÚNICA
    if st.sidebar.button("🔄 Atualizar Dados do Google Sheets", key="btn_atualizar_dados"):
        # Limpa todos os caches de dados
        st.cache_data.clear()
        st.success("✅ Cache limpo! Os dados serão atualizados na próxima leitura.")
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Clique no botão acima para atualizar os dados diretamente do Google Sheets")

    
# ==================== FUNÇÕES DE FILTRO ====================

def aplicar_filtro_data(df, coluna_data, data_inicio, data_fim):
    """
    Aplica filtro de data em um DataFrame
    """
    if df.empty:
        return df
    
    # Converter coluna de data para datetime se necessário
    if df[coluna_data].dtype == 'object':
        df[coluna_data] = pd.to_datetime(df[coluna_data], format='%d/%m/%Y', errors='coerce')
    
    # Aplicar filtro
    mask = (df[coluna_data] >= pd.to_datetime(data_inicio)) & (df[coluna_data] <= pd.to_datetime(data_fim))
    return df.loc[mask]

def criar_filtros_sidebar():
    """
    Cria filtros globais na sidebar
    """
    st.sidebar.header("🎛️ Filtros Globais")
    
    # Usar valores do session_state como padrão
    hoje = datetime.now()
    data_inicio_default = st.session_state.get('data_inicio', hoje - timedelta(days=30))
    data_fim_default = st.session_state.get('data_fim', hoje)
    
    # Filtro de período
    periodo = st.sidebar.selectbox(
        "Período",
        ["Personalizado", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Mês anterior", "Este trimestre"],
        key="filtro_periodo"
    )
    
    # Definir datas baseado no período selecionado
    if periodo == "Últimos 7 dias":
        data_inicio = hoje - timedelta(days=7)
        data_fim = hoje
    elif periodo == "Últimos 30 dias":
        data_inicio = hoje - timedelta(days=30)
        data_fim = hoje
    elif periodo == "Este mês":
        data_inicio = datetime(hoje.year, hoje.month, 1)
        data_fim = hoje
    elif periodo == "Mês anterior":
        primeiro_dia_mes_anterior = datetime(hoje.year, hoje.month - 1, 1) if hoje.month > 1 else datetime(hoje.year - 1, 12, 1)
        ultimo_dia_mes_anterior = datetime(hoje.year, hoje.month, 1) - timedelta(days=1)
        data_inicio = primeiro_dia_mes_anterior
        data_fim = ultimo_dia_mes_anterior
    elif periodo == "Este trimestre":
        trimestre_atual = (hoje.month - 1) // 3 + 1
        mes_inicio_trimestre = (trimestre_atual - 1) * 3 + 1
        data_inicio = datetime(hoje.year, mes_inicio_trimestre, 1)
        data_fim = hoje
    else:  # Personalizado
        col1, col2 = st.sidebar.columns(2)
        with col1:
            # Usar o valor atual do session_state como padrão
            data_inicio = st.date_input("Data início", value=data_inicio_default, key="data_inicio_input")
        with col2:
            data_fim = st.date_input("Data fim", value=data_fim_default, key="data_fim_input")
    
    # Atualizar session_state apenas se os valores mudaram
    if data_inicio != st.session_state.get('data_inicio'):
        st.session_state.data_inicio = data_inicio
    if data_fim != st.session_state.get('data_fim'):
        st.session_state.data_fim = data_fim
    
    return data_inicio, data_fim

# ==================== FUNÇÕES DE CARREGAMENTO ATUALIZADAS ====================
@st.cache_data(ttl=300)
def carregar_melhorias():
    try:
        # 🆕 USA CREDENCIAIS DO SECRETS
        if 'gcp_service_account' not in st.secrets:
            st.error("❌ Credenciais do Google Sheets não configuradas")
            return pd.DataFrame()
            
        service_account_info = dict(st.secrets['gcp_service_account'])
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit')
        aba = spreadsheet.worksheet("melhorias")
        dados = aba.get_all_records()
        df = pd.DataFrame(dados)
        
        if not df.empty and 'data_proposta' in df.columns:
            df['data_proposta'] = pd.to_datetime(df['data_proposta'], format='%d/%m/%Y', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar melhorias: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def carregar_cerimonias():
    try:
        # 🆕 USA CREDENCIAIS DO SECRETS
        if 'gcp_service_account' not in st.secrets:
            st.error("❌ Credenciais do Google Sheets não configuradas")
            return pd.DataFrame()
            
        service_account_info = dict(st.secrets['gcp_service_account'])
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit')
        aba = spreadsheet.worksheet("cerimonias_reunioes")
        dados = aba.get_all_records()
        df = pd.DataFrame(dados)
        
        if not df.empty and 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar cerimônias: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def carregar_demandas():
    try:
        # 🆕 USA CREDENCIAIS DO SECRETS
        if 'gcp_service_account' not in st.secrets:
            st.error("❌ Credenciais do Google Sheets não configuradas")
            return pd.DataFrame()
            
        service_account_info = dict(st.secrets['gcp_service_account'])
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit')
        aba = spreadsheet.worksheet("demandas_escritas")
        dados = aba.get_all_records()
        df = pd.DataFrame(dados)
        
        if not df.empty and 'data_avaliacao' in df.columns:
            df['data_avaliacao'] = pd.to_datetime(df['data_avaliacao'], format='%d/%m/%Y', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar demandas: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def carregar_documentos():
    try:
        # 🆕 USA CREDENCIAIS DO SECRETS
        if 'gcp_service_account' not in st.secrets:
            st.error("❌ Credenciais do Google Sheets não configuradas")
            return pd.DataFrame()
            
        service_account_info = dict(st.secrets['gcp_service_account'])
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit')
        aba = spreadsheet.worksheet("documentos_criterios")
        dados = aba.get_all_records()
        df = pd.DataFrame(dados)
        
        if not df.empty and 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar documentos: {e}")
        return pd.DataFrame()

# ==================== FUNÇÕES DE SALVAR CORRIGIDAS ====================
def salvar_melhoria(dados):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credenciais.json', scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit')
        
        aba = spreadsheet.worksheet("melhorias")
        
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
        
        aba.append_row(nova_linha)
        st.success("✅ Melhoria salva com sucesso!")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar melhoria: {e}")
        return False

def salvar_cerimonia(dados):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credenciais.json', scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit')
        
        aba = spreadsheet.worksheet("cerimonias_reunioes")
        
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
        
        aba.append_row(nova_linha)
        st.success("✅ Cerimônia/Reunião salva com sucesso!")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar cerimônia: {e}")
        return False

def salvar_demanda(dados):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credenciais.json', scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit')
        
        aba = spreadsheet.worksheet("demandas_escritas")
        
        nova_linha = [
            dados['data_avaliacao'].strftime('%d/%m/%Y'),
            dados['periodo'],
            dados['total_historias'],
            dados['historias_prioridade_definida'],
            dados['historias_criterio_aceite'],
            dados['status'],
            dados['observacoes']
        ]
        
        aba.append_row(nova_linha)
        st.success("✅ Avaliação de demandas salva com sucesso!")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar demanda: {e}")
        return False

def salvar_documento(dados):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credenciais.json', scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit')
        
        aba = spreadsheet.worksheet("documentos_criterios")
        
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
        
        aba.append_row(nova_linha)
        st.success("✅ Documento salvo com sucesso!")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar documento: {e}")
        return False

# ==================== INTERFACE MELHORIAS ====================
def pagina_melhorias(data_inicio, data_fim):
    st.header("💡 Sistema de Melhorias")
    
    # Filtros específicos da página - AGORA EM EXPANDER
    with st.expander("🔍 Filtros", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.multiselect(
                "Status",
                ["Proposta", "Em análise", "Aprovada", "Implementada"],
                default=[],  # ← MUDOU: estava com valores, agora vazio
                key="filtro_status_melhorias"
            )
        
        with col2:
            impacto_filter = st.multiselect(
                "Impacto",
                ["Alto", "Médio", "Baixo"],
                default=[],  # ← MUDOU: estava com valores, agora vazio
                key="filtro_impacto_melhorias"
            )
        
        with col3:
            aplicada_filter = st.selectbox(
                "Melhoria Aplicada",
                ["Todos", "SIM", "NÃO"],
                key="filtro_aplicada_melhorias"
            )
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Nova Melhoria", "📋 Dados"])
    
    with tab1:
        dados = carregar_melhorias()
    
        # Aplicar filtros apenas se algum foi selecionado
        if not dados.empty:
            df_filtrado = dados.copy()
        
            # Aplicar filtros apenas se foram selecionados
            if status_filter:
                df_filtrado = df_filtrado[df_filtrado['status'].isin(status_filter)]
        
            if impacto_filter:
                df_filtrado = df_filtrado[df_filtrado['impacto'].isin(impacto_filter)]
        
            if aplicada_filter != "Todos":
                valor_filtro = "SIM" if aplicada_filter == "SIM" else "NÃO"
                df_filtrado = df_filtrado[df_filtrado['melhoria_aplicada'] == valor_filtro]
        
            # Aplicar filtro de data (sempre aplica, pois vem dos filtros globais)
            if data_inicio and data_fim and 'data_proposta' in df_filtrado.columns:
                df_filtrado = aplicar_filtro_data(df_filtrado, 'data_proposta', data_inicio, data_fim)
        
            # USAR df_filtrado para as métricas
            dados_exibicao = df_filtrado
        else:
            dados_exibicao = dados
    
        if len(dados_exibicao) > 0:
            total = len(dados_exibicao)
            aplicadas = len(dados_exibicao[dados_exibicao['melhoria_aplicada'] == 'SIM'])
            taxa = (aplicadas / total * 100) if total > 0 else 0
        
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Melhorias", total)
            col2.metric("Aplicadas", aplicadas)
            col3.metric("Taxa", f"{taxa:.1f}%")
        
            # Gráfico
            fig = px.pie(
                names=['Aplicadas', 'Pendentes'],
                values=[aplicadas, total - aplicadas],
                title="Taxa de Aplicação de Melhorias"
            )
            st.plotly_chart(fig, use_container_width=True)
        
            # Mostrar informações sobre filtros aplicados
            filtros_ativos = []
            if status_filter:
                filtros_ativos.append(f"Status: {', '.join(status_filter)}")
            if impacto_filter:
                filtros_ativos.append(f"Impacto: {', '.join(impacto_filter)}")
            if aplicada_filter != "Todos":
                filtros_ativos.append(f"Aplicada: {aplicada_filter}")
        
            if filtros_ativos:
                st.info(f"🔍 Filtros ativos: {', '.join(filtros_ativos)}")
            
        else:
            # Mostrar mensagem mais específica
            if dados.empty:
                st.info("📝 Nenhuma melhoria registrada")
            else:
                st.info("🔍 Nenhuma melhoria encontrada com os filtros aplicados")
                st.write("💡 **Dica:** Tente ajustar os filtros ou limpar as seleções para ver todos os dados")

# ==================== PÁGINA CERIMÔNIAS ====================
def pagina_cerimonias(data_inicio, data_fim):
    st.header("📅 Cerimônias e Reuniões")
    
    # Filtros específicos - AGORA EM EXPANDER
    with st.expander("🔍 Filtros", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tipo_filter = st.multiselect(
                "Tipo",
                ["Cerimônia", "Reunião"],
                default=[],  # ← MUDOU: estava com valores, agora vazio
                key="filtro_tipo_cerimonias"
            )
        
        with col2:
            presente_filter = st.selectbox(
                "Presença",
                ["Todos", "SIM", "NÃO"],
                key="filtro_presenca_cerimonias"
            )
        
        with col3:
            nome_filter = st.text_input("Filtrar por nome", key="filtro_nome_cerimonias")
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Novo Registro", "📋 Dados"])
    
    with tab1:
        dados = carregar_cerimonias()
        
        if len(dados) > 0:
            # Métricas principais
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
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico por tipo
                tipo_count = dados['tipo'].value_counts()
                fig_tipo = px.pie(
                    names=tipo_count.index,
                    values=tipo_count.values,
                    title="Distribuição por Tipo"
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
            
            with col2:
                # Gráfico de tempo por tipo
                tempo_por_tipo = dados.groupby('tipo')['duracao_minutos'].sum().reset_index()
                fig_tempo = px.bar(
                    tempo_por_tipo,
                    x='tipo',
                    y='duracao_minutos',
                    title="Tempo Total por Tipo (minutos)"
                )
                st.plotly_chart(fig_tempo, use_container_width=True)
                
        else:
            st.info("Nenhuma cerimônia ou reunião registrada")
    
    with tab2:
        # CORREÇÃO: usar apenas key, não ambos
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
                dados = {
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
                if salvar_cerimonia(dados):
                    st.rerun()
    
    with tab3:
        dados = carregar_cerimonias()
        if not dados.empty:
            # Usar os parâmetros recebidos diretamente
            if data_inicio and data_fim:
                dados = aplicar_filtro_data(dados, 'data', data_inicio, data_fim)
            
            if tipo_filter:
                dados = dados[dados['tipo'].isin(tipo_filter)]
            if presente_filter != "Todos":
                dados = dados[dados['presente'] == presente_filter]
            if nome_filter:
                dados = dados[dados['nome'].str.contains(nome_filter, case=False, na=False)]
        
        st.dataframe(dados, use_container_width=True)

# ==================== PÁGINA DEMANDAS ESCRITAS ====================
def pagina_demandas(data_inicio, data_fim):
    st.header("📈 Demandas Escritas - A cada 15 dias")
    
    # Adicionar filtros específicos - AGORA EM EXPANDER
    with st.expander("🔍 Filtros", expanded=False):
        status_filter = st.multiselect(
            "Status das Demandas",
            ["Concluído", "Em andamento", "Pendente"],
            default=[],  # ← MUDOU: estava com valores, agora vazio
            key="filtro_status_demandas"
        )
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Nova Avaliação", "📋 Dados"])
    
    with tab1:
        dados = carregar_demandas()

        # Aplicar filtro de data
        if not dados.empty:
            # Usar os parâmetros recebidos diretamente
            if data_inicio and data_fim:
                dados = aplicar_filtro_data(dados, 'data_avaliacao', data_inicio, data_fim)
            
            # Aplicar filtro de status apenas se selecionado
            if status_filter:
                dados = dados[dados['status'].isin(status_filter)]
        
        if len(dados) > 0:
            # Métricas principais
            ultimo_periodo = dados.iloc[-1]
            taxa_prioridade = (ultimo_periodo['historias_prioridade_definida'] / ultimo_periodo['total_historias'] * 100) if ultimo_periodo['total_historias'] > 0 else 0
            taxa_criterio = (ultimo_periodo['historias_criterio_aceite'] / ultimo_periodo['total_historias'] * 100) if ultimo_periodo['total_historias'] > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Histórias", ultimo_periodo['total_historias'])
            col2.metric("Com Prioridade", ultimo_periodo['historias_prioridade_definida'])
            col3.metric("Taxa Prioridade", f"{taxa_prioridade:.1f}%", 
                       delta=f"{taxa_prioridade - 100:.1f}%" if taxa_prioridade < 100 else None,
                       delta_color="inverse" if taxa_prioridade < 100 else "normal")
            col4.metric("Taxa Critério Aceite", f"{taxa_criterio:.1f}%")
            
            # Gráfico de evolução
            if len(dados) > 1:
                st.subheader("📈 Evolução ao Longo do Tempo")
                dados['taxa_prioridade'] = (dados['historias_prioridade_definida'] / dados['total_historias'] * 100).round(1)
                dados['taxa_criterio'] = (dados['historias_criterio_aceite'] / dados['total_historias'] * 100).round(1)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dados['periodo'], y=dados['taxa_prioridade'], 
                                       name='% Prioridade Definida', line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=dados['periodo'], y=dados['taxa_criterio'], 
                                       name='% Critério Aceite', line=dict(color='green')))
                fig.update_layout(title="Evolução das Taxas por Período")
                st.plotly_chart(fig, use_container_width=True)
                
        else:
            st.info("Nenhuma avaliação de demandas registrada")
    
    with tab2:
        with st.form(key="form_demanda"):
            col1, col2 = st.columns(2)
            
            with col1:
                data_avaliacao = st.date_input("Data da Avaliação", datetime.now(), key="data_avaliacao_demanda")
                periodo = st.text_input("Período", placeholder="01-15/Nov, 16-30/Nov...", key="periodo_demanda")
                total_historias = st.number_input("Total de Histórias", min_value=0, value=0, key="total_historias_demanda")
                status = st.selectbox("Status", ["Concluído", "Em andamento", "Pendente"], key="status_demanda")
            
            with col2:
                historias_prioridade = st.number_input("Histórias com Prioridade Definida", min_value=0, value=0, key="prioridade_demanda")
                historias_criterio = st.number_input("Histórias com Critério de Aceite", min_value=0, value=0, key="criterio_demanda")
                observacoes = st.text_area("Observações", placeholder="Aguardando priorização, etc...", key="observacoes_demanda")
            
            if st.form_submit_button("💾 Salvar Avaliação", key="btn_salvar_demanda"):
                if total_historias > 0 and historias_prioridade <= total_historias and historias_criterio <= total_historias:
                    dados = {
                        'data_avaliacao': data_avaliacao,
                        'periodo': periodo,
                        'total_historias': total_historias,
                        'historias_prioridade_definida': historias_prioridade,
                        'historias_criterio_aceite': historias_criterio,
                        'status': status,
                        'observacoes': observacoes
                    }
                    if salvar_demanda(dados):
                        st.rerun()
                else:
                    st.error("Verifique os números: Prioridade e Critério não podem ser maiores que o Total")
    
    with tab3:
        dados = carregar_demandas()
        if len(dados) > 0:
            # Adicionar colunas calculadas
            dados['%_prioridade'] = (dados['historias_prioridade_definida'] / dados['total_historias'] * 100).round(1)
            dados['%_criterio'] = (dados['historias_criterio_aceite'] / dados['total_historias'] * 100).round(1)
            st.dataframe(dados, use_container_width=True)
        else:
            st.info("Nenhum dado disponível")

# ==================== PÁGINA DOCUMENTOS ENTREGUES ====================
def pagina_documentos(data_inicio, data_fim):
    st.header("📋 Documentos Elaborados e Entregues")

    # Adicionar filtros específicos - AGORA EM EXPANDER
    with st.expander("🔍 Filtros", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_doc_filter = st.multiselect(
                "Tipo de Documento",
                ["User Story", "Especificação", "Layout", "Processo", "Relatório", "Critérios de Aceite"],
                default=[],  # ← MUDOU: estava com valores, agora vazio
                key="filtro_tipo_documentos"
            )
        
        with col2:
            status_doc_filter = st.multiselect(
                "Status",
                ["Rascunho", "Revisão", "Aprovado", "Entregue"],
                default=[],  # ← MUDOU: estava com valores, agora vazio
                key="filtro_status_documentos"
            )
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Novo Documento", "📋 Dados"])
    
    with tab1:
        dados = carregar_documentos()

        # Aplicar filtros
        if not dados.empty:
            # Usar os parâmetros recebidos diretamente
            if data_inicio and data_fim:
                dados = aplicar_filtro_data(dados, 'data', data_inicio, data_fim)
            
            if tipo_doc_filter:
                dados = dados[dados['tipo_documento'].isin(tipo_doc_filter)]
            if status_doc_filter:
                dados = dados[dados['status'].isin(status_doc_filter)]
        
        if len(dados) > 0:
            # Métricas principais
            total_documentos = len(dados)
            docs_criterios = len(dados[dados['critérios_aceite'] == 'SIM'])
            docs_templates = len(dados[dados['template_padronizado'] == 'SIM'])
            tempo_total = dados['tempo_minutos'].sum()
            tempo_medio = tempo_total / total_documentos if total_documentos > 0 else 0
            
            # Cálculo das taxas
            taxa_criterios = (docs_criterios / total_documentos * 100) if total_documentos > 0 else 0
            taxa_templates = (docs_templates / total_documentos * 100) if total_documentos > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Documentos", total_documentos)
            col2.metric("Taxa Critérios", f"{taxa_criterios:.1f}%")
            col3.metric("Taxa Templates", f"{taxa_templates:.1f}%")
            col4.metric("Tempo Médio", f"{tempo_medio:.0f} min")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico por tipo de documento
                tipo_count = dados['tipo_documento'].value_counts()
                fig_tipo = px.pie(
                    names=tipo_count.index,
                    values=tipo_count.values,
                    title="Distribuição por Tipo de Documento"
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
            
            with col2:
                # Gráfico de tempo por tipo
                tempo_por_tipo = dados.groupby('tipo_documento')['tempo_minutos'].mean().reset_index()
                fig_tempo = px.bar(
                    tempo_por_tipo,
                    x='tipo_documento',
                    y='tempo_minutos',
                    title="Tempo Médio por Tipo (minutos)"
                )
                st.plotly_chart(fig_tempo, use_container_width=True)
            
            # Análise de produtividade
            st.subheader("⏱️ Análise de Produtividade")
            horas_totais = tempo_total / 60
            dias_trabalho = len(dados['data'].unique())
            horas_por_dia = horas_totais / dias_trabalho if dias_trabalho > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Horas Totais", f"{horas_totais:.1f}h")
            col2.metric("Dias com Documentação", dias_trabalho)
            col3.metric("Média Diária", f"{horas_por_dia:.1f}h/dia")
                
        else:
            st.info("Nenhum documento registrado")
    
    with tab2:
        # CORREÇÃO: usar apenas key, não ambos
        with st.form(key="form_documento"):
            col1, col2 = st.columns(2)
            
            with col1:
                data = st.date_input("Data de Entrega", datetime.now(), key="data_documento")
                tipo_documento = st.selectbox("Tipo de Documento", 
                    ["User Story", "Especificação", "Layout", "Processo", "Relatório", "Critérios de Aceite"], key="tipo_documento")
                nome_documento = st.text_input("Nome do Documento", placeholder="US-001 - Login, Fluxo de Pagamento...", key="nome_documento")
                tempo_minutos = st.number_input("Tempo Gasto (minutos)", min_value=1, value=60, key="tempo_documento")
                status = st.selectbox("Status", ["Rascunho", "Revisão", "Aprovado", "Entregue"], key="status_documento")
            
            with col2:
                criterios_aceite = st.checkbox("Possui critérios de aceite claros?", value=True, key="criterios_documento")
                template_padronizado = st.checkbox("Usa template padronizado?", value=True, key="template_documento")
                observacoes = st.text_area("Observações", placeholder="Dificuldades, feedbacks, etc...", key="observacoes_documento")
            
            if st.form_submit_button("💾 Salvar Documento", key="btn_salvar_documento"):
                dados = {
                    'data': data,
                    'tipo_documento': tipo_documento,
                    'nome_documento': nome_documento,
                    'tempo_minutos': tempo_minutos,
                    'critérios_aceite': criterios_aceite,
                    'template_padronizado': template_padronizado,
                    'status': status,
                    'observacoes': observacoes
                }
                if salvar_documento(dados):
                    st.rerun()
    
    with tab3:
        dados = carregar_documentos()
        if len(dados) > 0:
            st.dataframe(dados, use_container_width=True)
        else:
            st.info("Nenhum documento disponível")

# ==================== FUNÇÂO IA =========================

def pagina_ia_assistente(data_inicio, data_fim):
    st.header("🤖 Assistente de IA - Análise de PO")
    
    # Carregar todos os dados
    dados_disponiveis = {
        'melhorias': carregar_melhorias(),
        'cerimonias': carregar_cerimonias(),
        'demandas': carregar_demandas(),
        'documentos': carregar_documentos()
    }
    
    # Aplicar filtros de data em todos os datasets
    for categoria, df in dados_disponiveis.items():
        if not df.empty:
            coluna_data = None
            if categoria == 'melhorias' and 'data_proposta' in df.columns:
                coluna_data = 'data_proposta'
            elif categoria == 'cerimonias' and 'data' in df.columns:
                coluna_data = 'data'
            elif categoria == 'demandas' and 'data_avaliacao' in df.columns:
                coluna_data = 'data_avaliacao'
            elif categoria == 'documentos' and 'data' in df.columns:
                coluna_data = 'data'
            
            if coluna_data and data_inicio and data_fim:
                dados_disponiveis[categoria] = aplicar_filtro_data(df, coluna_data, data_inicio, data_fim)
    
    # Interface do assistente
    st.markdown("""
    ### 💬 Faça perguntas sobre seus dados de Product Ownership
    
    **Exemplos de perguntas:**
    - "Como está minha performance nas cerimônias ágeis?"
    - "Qual a eficiência na documentação das user stories?"
    - "Quais melhorias posso implementar no processo de priorização?"
    - "Analise minha produtividade nos últimos 30 dias"
    - "Quais são meus principais pontos de melhoria como PO?"
    - "Como melhorar a qualidade dos critérios de aceite?"
    """)
    
    pergunta = st.text_area(
        "Sua pergunta:",
        placeholder="Ex: Analise minha eficiência na documentação e sugira melhorias...",
        height=100,
        key="pergunta_ia"
    )
    
    if st.button("🔍 Analisar com IA", type="primary", key="btn_analisar_ia"):
        if pergunta.strip():
            with st.spinner("🤖 Analisando dados e gerando insights..."):
                # Usar a chave do secrets
                try:
                    gemini_key = st.secrets['gemini']['api_key']
                except:
                    gemini_key = None
                    st.warning("⚠️ Chave Gemini não encontrada nos secrets")
                
                resposta = consultar_assistente_po(
                    pergunta=pergunta,
                    dados_disponiveis=dados_disponiveis,
                    gemini_key=gemini_key
                )
                
            st.markdown("---")
            st.markdown("### 📊 Resposta da Análise")
            st.markdown(resposta)
        else:
            st.warning("⚠️ Por favor, digite uma pergunta para análise.")

    # Estatísticas rápidas
    st.markdown("---")
    st.subheader("📈 Dados Disponíveis para Análise")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Melhorias", len(dados_disponiveis['melhorias']))
    with col2:
        st.metric("Cerimônias", len(dados_disponiveis['cerimonias']))
    with col3:
        st.metric("Demandas", len(dados_disponiveis['demandas']))
    with col4:
        st.metric("Documentos", len(dados_disponiveis['documentos']))

# ==================== MENU PRINCIPAL ====================
def main():
    # Inicializar session_state se não existir - ANTES de qualquer widget
    if 'data_inicio' not in st.session_state:
        st.session_state.data_inicio = datetime.now() - timedelta(days=30)
    if 'data_fim' not in st.session_state:
        st.session_state.data_fim = datetime.now()
    
    # Chamar a função create_sidebar() para exibir o botão de atualização
    create_sidebar()
    
    st.title("📊 Sistema PO - Indicadores Estratégicos")

    # Criar filtros globais na sidebar
    data_inicio, data_fim = criar_filtros_sidebar()
    
    # Botão para limpar filtros - COM KEY ÚNICA
    if st.sidebar.button("🗑️ Limpar Filtros", key="btn_limpar_filtros"):
        # Limpar apenas os dados, mantendo a estrutura do session_state
        for key in list(st.session_state.keys()):
            if key not in ['data_inicio', 'data_fim']:
                del st.session_state[key]
        st.rerun()
    
    # Mostrar período atual selecionado
    st.sidebar.info(f"**Período selecionado:**\n{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    
    # 🆕 MENU ATUALIZADO COM ASSISTENTE IA
    menu = st.sidebar.selectbox(
        "Navegação",
        ["💡 Melhorias", "📅 Cerimônias", "📈 Demandas", "📋 Documentos", "🤖 Assistente IA"],  # ← ADICIONEI AQUI
        key="menu_principal"
    )
    
    # 🆕 PASSE OS FILTROS PARA A NOVA PÁGINA TAMBÉM
    if menu == "💡 Melhorias":
        pagina_melhorias(data_inicio, data_fim)
    elif menu == "📅 Cerimônias":
        pagina_cerimonias(data_inicio, data_fim)
    elif menu == "📈 Demandas":
        pagina_demandas(data_inicio, data_fim)
    elif menu == "📋 Documentos":
        pagina_documentos(data_inicio, data_fim)
    elif menu == "🤖 Assistente IA":  # ← ADICIONEI ESTA CONDIÇÃO
        pagina_ia_assistente(data_inicio, data_fim)

if __name__ == "__main__":
    main()