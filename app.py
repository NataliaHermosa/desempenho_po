import streamlit as st
import pandas as pd
import gspread
import plotly.graph_objects as go 
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Sistema PO - Indicadores Estratégicos",
    page_icon="📊",
    layout="wide"
)

# ==================== CONEXÃO GOOGLE SHEETS ====================
def conectar_google_sheets():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('credenciais.json', scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_url('https://docs.google.com/spreadsheets/d/12Nn4aRW_-yVTB1itRrY0Ae1mhETVTXwZiRzezAzwRcQ/edit')

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
    
    # Filtro de período
    periodo = st.sidebar.selectbox(
        "Período",
        ["Personalizado", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Mês anterior", "Este trimestre"]
    )
    
    # Definir datas baseado no período selecionado
    hoje = datetime.now()
    
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
            data_inicio = st.date_input("Data início", hoje - timedelta(days=30))
        with col2:
            data_fim = st.date_input("Data fim", hoje)
    
    return data_inicio, data_fim

# ==================== FUNÇÕES MELHORIAS ====================
def carregar_melhorias():
    planilha = conectar_google_sheets()
    aba = planilha.worksheet("melhorias")
    dados = aba.get_all_records()
    return pd.DataFrame(dados)

def salvar_melhoria(dados):
    planilha = conectar_google_sheets()
    aba = planilha.worksheet("melhorias")
    
    nova_linha = [
        dados['data_proposta'].strftime('%d/%m/%Y'),
        dados['melhoria_id'],
        dados['melhoria_proposta'],
        dados['descricao_detalhada'],
        dados['beneficio_esperado'],
        "SIM" if dados['melhoria_aplicada'] else "NÃO",
        dados['data_aplicacao'].strftime('%d/%m/%Y') if dados.get('data_aplicacao') else "",
        dados['status'],
        dados['impacto']
    ]
    
    aba.append_row(nova_linha)
    return True

# ==================== FUNÇÕES CERIMÔNIAS ====================
def carregar_cerimonias():
    planilha = conectar_google_sheets()
    aba = planilha.worksheet("cerimonias_reunioes")
    dados = aba.get_all_records()
    df = pd.DataFrame(dados)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y', errors='coerce')
    
    return df

def salvar_cerimonia(dados):
    planilha = conectar_google_sheets()
    aba = planilha.worksheet("cerimonias_reunioes")
    
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
    return True

# ==================== FUNÇÕES DEMANDAS ESCRITAS ====================
def carregar_demandas():
    planilha = conectar_google_sheets()
    aba = planilha.worksheet("demandas_escritas")
    dados = aba.get_all_records()
    df = pd.DataFrame(dados)
    
    if not df.empty:
        df['data_avaliacao'] = pd.to_datetime(df['data_avaliacao'], format='%d/%m/%Y', errors='coerce')
    
    return df
def salvar_demanda(dados):
    planilha = conectar_google_sheets()
    aba = planilha.worksheet("demandas_escritas")
    
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
    return True

# ==================== FUNÇÕES DOCUMENTOS ENTREGUES ====================
def carregar_documentos():
    planilha = conectar_google_sheets()
    aba = planilha.worksheet("documentos_criterios")
    dados = aba.get_all_records()
    df = pd.DataFrame(dados)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y', errors='coerce')
    
    return df

def salvar_documento(dados):
    planilha = conectar_google_sheets()
    aba = planilha.worksheet("documentos_criterios")
    
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
    return True

# ==================== INTERFACE MELHORIAS ====================
def pagina_melhorias():
    st.header("💡 Sistema de Melhorias")
    
    # Filtros específicos da página
    st.subheader("🔍 Filtros")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Status",
            ["Proposta", "Em análise", "Aprovada", "Implementada"],
            default=["Proposta", "Em análise", "Aprovada", "Implementada"]
        )
    
    with col2:
        impacto_filter = st.multiselect(
            "Impacto",
            ["Alto", "Médio", "Baixo"],
            default=["Alto", "Médio", "Baixo"]
        )
    
    with col3:
        aplicada_filter = st.selectbox(
            "Melhoria Aplicada",
            ["Todos", "SIM", "NÃO"]
        )
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Nova Melhoria", "📋 Dados"])
    
    with tab1:
        dados = carregar_melhorias()
        
        if len(dados) > 0:
            total = len(dados)
            aplicadas = len(dados[dados['melhoria_aplicada'] == 'SIM'])
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
        else:
            st.info("Nenhuma melhoria registrada")
    
    with tab2:
        with st.form("form_melhoria"):
            col1, col2 = st.columns(2)
            
            with col1:
                data = st.date_input("Data", datetime.now())
                id_melhoria = st.text_input("ID Card Jira", "TE-50")
                proposta = st.text_input("Melhoria Proposta")
                impacto = st.selectbox("Impacto", ["Alto", "Médio", "Baixo"])
            
            with col2:
                descricao = st.text_area("Descrição")
                beneficio = st.text_area("Benefício Esperado")
                aplicada = st.checkbox("Já aplicada?")
                status = st.selectbox("Status", ["Proposta", "Em análise", "Aprovada", "Implementada"])
            
            if st.form_submit_button("💾 Salvar"):
                dados = {
                    'data_proposta': data,
                    'melhoria_id': id_melhoria,
                    'melhoria_proposta': proposta,
                    'descricao_detalhada': descricao,
                    'beneficio_esperado': beneficio,
                    'melhoria_aplicada': aplicada,
                    'status': status,
                    'impacto': impacto
                }
                salvar_melhoria(dados)
                st.success("Salvo com sucesso!")
    
    with tab3:
        dados = carregar_melhorias()
        st.dataframe(dados, use_container_width=True)

# ==================== PÁGINA CERIMÔNIAS ====================
def pagina_cerimonias():
    st.header("📅 Cerimônias e Reuniões")
    
    # Filtros específicos
    st.subheader("🔍 Filtros")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_filter = st.multiselect(
            "Tipo",
            ["Cerimônia", "Reunião"],
            default=["Cerimônia", "Reunião"]
        )
    
    with col2:
        presente_filter = st.selectbox(
            "Presença",
            ["Todos", "SIM", "NÃO"]
        )
    
    with col3:
        nome_filter = st.text_input("Filtrar por nome")
    
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
        with st.form("form_cerimonia"):
            col1, col2 = st.columns(2)
            
            with col1:
                data = st.date_input("Data", datetime.now())
                tipo = st.selectbox("Tipo", ["Cerimônia", "Reunião"])
                nome = st.text_input("Nome", placeholder="Daily, Planning, Review...")
                presente = st.checkbox("Presente?", value=True)
                duracao = st.number_input("Duração (minutos)", min_value=1, value=30)
            
            with col2:
                participantes = st.text_input("Participantes", placeholder="PO, Devs, QA...")
                objetivo = st.text_area("Objetivo")
                decisoes = st.text_area("Decisões/Ações")
                resultado = st.text_area("Resultado")
            
            if st.form_submit_button("💾 Salvar Cerimônia/Reunião"):
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
                salvar_cerimonia(dados)
                st.success("Cerimônia/Reunião salva com sucesso!")
    
    with tab3:
        dados = carregar_cerimonias()
        if not dados.empty:
            data_inicio, data_fim = st.session_state.get('data_inicio'), st.session_state.get('data_fim')
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
# (Implementar padrão similar para as outras páginas)

def pagina_demandas():
    st.header("📈 Demandas Escritas - A cada 15 dias")
    
    # Adicionar filtros específicos similares às outras páginas
    st.subheader("🔍 Filtros")
    
    status_filter = st.multiselect(
        "Status das Demandas",
        ["Concluído", "Em andamento", "Pendente"],
        default=["Concluído", "Em andamento", "Pendente"]
    )
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Nova Avaliação", "📋 Dados"])
    
    with tab1:
        dados = carregar_demandas()

        # Aplicar filtro de data
        if not dados.empty:
            data_inicio, data_fim = st.session_state.get('data_inicio'), st.session_state.get('data_fim')
            if data_inicio and data_fim:
                dados = aplicar_filtro_data(dados, 'data_avaliacao', data_inicio, data_fim)
            
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
        with st.form("form_demanda"):
            col1, col2 = st.columns(2)
            
            with col1:
                data_avaliacao = st.date_input("Data da Avaliação", datetime.now())
                periodo = st.text_input("Período", placeholder="01-15/Nov, 16-30/Nov...")
                total_historias = st.number_input("Total de Histórias", min_value=0, value=0)
                status = st.selectbox("Status", ["Concluído", "Em andamento", "Pendente"])
            
            with col2:
                historias_prioridade = st.number_input("Histórias com Prioridade Definida", min_value=0, value=0)
                historias_criterio = st.number_input("Histórias com Critério de Aceite", min_value=0, value=0)
                observacoes = st.text_area("Observações", placeholder="Aguardando priorização, etc...")
            
            if st.form_submit_button("💾 Salvar Avaliação"):
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
                    salvar_demanda(dados)
                    st.success("Avaliação salva com sucesso!")
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
def pagina_documentos():
    st.header("📋 Documentos Elaborados e Entregues")

        # Adicionar filtros específicos
    st.subheader("🔍 Filtros")
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_doc_filter = st.multiselect(
            "Tipo de Documento",
            ["User Story", "Especificação", "Layout", "Processo", "Relatório", "Critérios de Aceite"],
            default=["User Story", "Especificação", "Layout", "Processo", "Relatório", "Critérios de Aceite"]
        )
    
    with col2:
        status_doc_filter = st.multiselect(
            "Status",
            ["Rascunho", "Revisão", "Aprovado", "Entregue"],
            default=["Rascunho", "Revisão", "Aprovado", "Entregue"]
        )
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Novo Documento", "📋 Dados"])
    
    with tab1:
        dados = carregar_documentos()

         # Aplicar filtros
        if not dados.empty:
            data_inicio, data_fim = st.session_state.get('data_inicio'), st.session_state.get('data_fim')
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
        with st.form("form_documento"):
            col1, col2 = st.columns(2)
            
            with col1:
                data = st.date_input("Data de Entrega", datetime.now())
                tipo_documento = st.selectbox("Tipo de Documento", 
                    ["User Story", "Especificação", "Layout", "Processo", "Relatório", "Critérios de Aceite"])
                nome_documento = st.text_input("Nome do Documento", placeholder="US-001 - Login, Fluxo de Pagamento...")
                tempo_minutos = st.number_input("Tempo Gasto (minutos)", min_value=1, value=60)
                status = st.selectbox("Status", ["Rascunho", "Revisão", "Aprovado", "Entregue"])
            
            with col2:
                criterios_aceite = st.checkbox("Possui critérios de aceite claros?", value=True)
                template_padronizado = st.checkbox("Usa template padronizado?", value=True)
                observacoes = st.text_area("Observações", placeholder="Dificuldades, feedbacks, etc...")
            
            if st.form_submit_button("💾 Salvar Documento"):
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
                salvar_documento(dados)
                st.success("Documento salvo com sucesso!")
    
    with tab3:
        dados = carregar_documentos()
        if len(dados) > 0:
            st.dataframe(dados, use_container_width=True)
        else:
            st.info("Nenhum documento disponível")

# ==================== MENU PRINCIPAL ====================
def main():
    st.title("📊 Sistema PO - Indicadores Estratégicos")

    # Criar filtros globais na sidebar
    data_inicio, data_fim = criar_filtros_sidebar()
    
    # Armazenar filtros na session state
    st.session_state['data_inicio'] = data_inicio
    st.session_state['data_fim'] = data_fim
    
    # Botão para limpar filtros
    if st.sidebar.button("🔄 Limpar Filtros"):
        st.session_state.clear()
        st.rerun()
    
    # Mostrar período atual selecionado
    st.sidebar.info(f"**Período selecionado:**\n{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    
    menu = st.sidebar.selectbox(
        "Navegação",
        ["💡 Melhorias", "📅 Cerimônias", "📈 Demandas", "📋 Documentos"]
    )
    
    if menu == "💡 Melhorias":
        pagina_melhorias()
    elif menu == "📅 Cerimônias":
        pagina_cerimonias()
    elif menu == "📈 Demandas":
        pagina_demandas()
    elif menu == "📋 Documentos":
        pagina_documentos()

if __name__ == "__main__":
    main()