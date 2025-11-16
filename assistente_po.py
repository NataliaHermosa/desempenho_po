import google.generativeai as genai
import pandas as pd
from datetime import datetime
import numpy as np
import os
import streamlit as st
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

def consultar_assistente_po(pergunta, dados_disponiveis, tipo_modelo="Gemini Pro", gemini_key=None):
    """
    Função principal do assistente para análise de dados de Product Owner.
    """
    
    # 🆕 BUSCA SEGURA DA CHAVE - ORDEM DE PRIORIDADE:
    # 1. Parâmetro da função (gemini_key)
    # 2. Variável de ambiente (.env)
    # 3. Secrets do Streamlit (se disponível)
    
    if not gemini_key:
        gemini_key = os.getenv('GEMINI_API_KEY')
    
    # Se ainda não encontrou e está no Streamlit, tenta secrets
    if not gemini_key and hasattr(st, 'secrets'):
        try:
            gemini_key = st.secrets.get('GEMINI_API_KEY')
        except:
            pass
    
    # 1. VERIFICAÇÃO CRÍTICA DA CHAVE
    if not gemini_key:
        error_msg = "❌ Chave da API Gemini não encontrada. Verifique seu arquivo .env ou configurações."
        print(error_msg)
        st.warning("Modo fallback ativado - usando análise local sem IA")
        return analise_local_po(pergunta, dados_disponiveis, is_fallback_mode=True)
    
    # 2. CONFIGURAÇÃO E EXECUÇÃO DA IA
    try:
        genai.configure(api_key=gemini_key)
        
        # 3. VERIFICAÇÃO DOS DADOS
        if not dados_disponiveis or all(df.empty for df in dados_disponiveis.values()):
            return "❌ Não há dados disponíveis para análise com os filtros atuais."
        
        print(f"🔍 Consultando Gemini para análise de PO: {pergunta}")
        
        # 4. Escolher modelo - VERSÕES CORRETAS
        if "Pro" in tipo_modelo:
            modelo_gemini = "gemini-2.5-pro"
        else:
            modelo_gemini = "gemini-2.0-flash" 

        # 5. Criar relatório COMPLETO específico para PO
        relatorio_completo = criar_relatorio_po_completo(dados_disponiveis, pergunta)

        # 6. Configurar e chamar o modelo
        model = genai.GenerativeModel(modelo_gemini)

        # 7. Prompt ESPECIALIZADO EM ANÁLISE DE PO
        prompt = f"""
        VOCÊ: Especialista em Product Ownership, Agile methodologies e análise de performance de PO

        DADOS COMPLETOS DISPONÍVEIS:
        {relatorio_completo}

        PERGUNTA DO USUÁRIO: {pergunta}

        CONTEXTO DAS ÁREAS DE DADOS:
        - MELHORIAS: melhoria_id, data_proposta, melhoria_proposta, descricao_detalhada, beneficio_esperado, melhoria_aplicada, data_aplicacao, status, impacto
        - CERIMÔNIAS: data, tipo, nome, presente, duracao_minutos, participantes, objetivo, decisoes_acoes, resultado
        - DEMANDAS: data_avaliacao, periodo, total_historias, historias_prioridade_definida, historias_criterio_aceite, status, observacoes
        - DOCUMENTOS: data, tipo_documento, nome_documento, tempo_minutos, critérios_aceite, template_padronizado, status, observacoes

        NOVAS INSTRUÇÕES ESPECÍFICAS:
        - Para perguntas sobre "dia mais produtivo", analise: documentos produzidos, tempo gasto, cerimônias participadas, melhorias propostas
        - Calcule eficiência: documentos por hora, tempo médio por documento, taxa de conclusão
        - Identifique padrões: dias da semana mais produtivos, relação entre tempo gasto e qualidade
        - Analise qualidade: critérios de aceite, uso de templates, resultados das cerimônias
        - Compare performance entre diferentes tipos de atividades
        - Dê respostas específicas com datas, números concretos e métricas calculadas
        - Sugira melhorias baseadas em padrões identificados nos dados

        FORMATO DA RESPOSTA:
        ## 🎯 Resposta Direta
        [Responda diretamente à pergunta com dados específicos]

        ## 📊 Análise Detalhada
        [Métricas calculadas, datas específicas, comparações]

        ## 🔍 Insights Identificados
        [Padrões, correlações, comportamentos observados]

        ## 💡 Recomendações Práticas
        [Sugestões baseadas nos dados para melhorar performance]

        RESPOSTA:
        """
        
        # ✅ AQUI ENTRA O PEDAÇO QUE VOCÊ PERGUNTOU:
        # Resto da sua lógica de chamada à API...
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        error_msg = f"❌ Erro na consulta à IA: {str(e)}"
        print(error_msg)
        return analise_local_po(pergunta, dados_disponiveis, is_fallback_mode=True)

# ✅ FORA DA FUNÇÃO PRINCIPAL - TESTE TEMPORÁRIO
# Teste temporário - depois remova
def testar_chave():
    load_dotenv()
    chave = os.getenv('GEMINI_API_KEY')
    if chave:
        print("✅ Chave carregada com sucesso do .env!")
        return True
    else:
        print("❌ Chave NÃO encontrada no .env")
        return False

# Execute este teste uma vez
testar_chave()

def criar_relatorio_po_completo(dados_disponiveis, pergunta):
    """Cria relatório MEGA COMPLETO para análise de Product Ownership"""
    
    relatorio = "=== ANÁLISE COMPLETA DE DADOS DE PRODUCT OWNERSHIP ===\n\n"
    pergunta_lower = pergunta.lower()
    
    # 🆕 ANÁLISE DIÁRIA DETALHADA PARA PERGUNTAS SOBRE PRODUTIVIDADE
    if any(palavra in pergunta_lower for palavra in ['dia', 'diário', 'produtividade', 'produtivo', 'produziu', 'melhor dia']):
        relatorio += "📅 ANÁLISE DIÁRIA DETALHADA (Produtividade):\n"
        
        dias_analisados = {}
        
        # Analisar produtividade por dia em CERIMÔNIAS
        if 'cerimonias' in dados_disponiveis and not dados_disponiveis['cerimonias'].empty:
            df_cerimonias = dados_disponiveis['cerimonias'].copy()
            if 'data' in df_cerimonias.columns:
                try:
                    df_cerimonias['data'] = pd.to_datetime(df_cerimonias['data'], errors='coerce')
                    df_cerimonias = df_cerimonias.dropna(subset=['data'])
                    
                    if not df_cerimonias.empty:
                        # Dias com mais cerimônias
                        cerimonias_por_dia = df_cerimonias.groupby(df_cerimonias['data'].dt.date).size()
                        if len(cerimonias_por_dia) > 0:
                            dia_mais_cerimonias = cerimonias_por_dia.idxmax()
                            qtd_mais_cerimonias = cerimonias_por_dia.max()
                            relatorio += f"• Dia com mais cerimônias: {dia_mais_cerimonias} ({qtd_mais_cerimonias} cerimônias)\n"
                            dias_analisados[dia_mais_cerimonias] = dias_analisados.get(dia_mais_cerimonias, 0) + qtd_mais_cerimonias
                        
                        # Tempo total por dia
                        if 'duracao_minutos' in df_cerimonias.columns:
                            tempo_por_dia = df_cerimonias.groupby(df_cerimonias['data'].dt.date)['duracao_minutos'].sum()
                            if len(tempo_por_dia) > 0:
                                dia_mais_tempo = tempo_por_dia.idxmax()
                                tempo_max = tempo_por_dia.max()
                                relatorio += f"• Dia com mais tempo em reuniões: {dia_mais_tempo} ({tempo_max}min = {tempo_max/60:.1f}h)\n"
                except Exception as e:
                    relatorio += f"• Erro na análise de cerimônias: {str(e)}\n"
        
        # Analisar produtividade por dia em DOCUMENTOS
        if 'documentos' in dados_disponiveis and not dados_disponiveis['documentos'].empty:
            df_documentos = dados_disponiveis['documentos'].copy()
            if 'data' in df_documentos.columns:
                try:
                    df_documentos['data'] = pd.to_datetime(df_documentos['data'], errors='coerce')
                    df_documentos = df_documentos.dropna(subset=['data'])
                    
                    if not df_documentos.empty:
                        # Dias com mais documentos
                        documentos_por_dia = df_documentos.groupby(df_documentos['data'].dt.date).size()
                        if len(documentos_por_dia) > 0:
                            dia_mais_documentos = documentos_por_dia.idxmax()
                            qtd_mais_documentos = documentos_por_dia.max()
                            relatorio += f"• Dia com mais documentos: {dia_mais_documentos} ({qtd_mais_documentos} documentos)\n"
                            dias_analisados[dia_mais_documentos] = dias_analisados.get(dia_mais_documentos, 0) + qtd_mais_documentos * 2  # Peso maior para documentos
                        
                        # Tempo de documentação por dia
                        if 'tempo_minutos' in df_documentos.columns:
                            tempo_doc_por_dia = df_documentos.groupby(df_documentos['data'].dt.date)['tempo_minutos'].sum()
                            if len(tempo_doc_por_dia) > 0:
                                dia_mais_tempo_doc = tempo_doc_por_dia.idxmax()
                                tempo_doc_max = tempo_doc_por_dia.max()
                                relatorio += f"• Dia com mais tempo em documentação: {dia_mais_tempo_doc} ({tempo_doc_max}min = {tempo_doc_max/60:.1f}h)\n"
                                
                                # Calcular produtividade por dia (documentos + tempo)
                                produtividade_por_dia = df_documentos.groupby(df_documentos['data'].dt.date).agg({
                                    'tempo_minutos': 'sum',
                                    'nome_documento': 'count'
                                })
                                produtividade_por_dia['eficiencia'] = produtividade_por_dia['nome_documento'] / (produtividade_por_dia['tempo_minutos'] / 60)  # docs por hora
                                
                                dia_mais_eficiente = produtividade_por_dia['eficiencia'].idxmax()
                                eficiencia_max = produtividade_por_dia['eficiencia'].max()
                                relatorio += f"• Dia mais eficiente em documentação: {dia_mais_eficiente} ({eficiencia_max:.1f} docs/hora)\n"
                except Exception as e:
                    relatorio += f"• Erro na análise de documentos: {str(e)}\n"
        
        # Analisar MELHORIAS por dia
        if 'melhorias' in dados_disponiveis and not dados_disponiveis['melhorias'].empty:
            df_melhorias = dados_disponiveis['melhorias'].copy()
            if 'data_proposta' in df_melhorias.columns:
                try:
                    df_melhorias['data_proposta'] = pd.to_datetime(df_melhorias['data_proposta'], errors='coerce')
                    df_melhorias = df_melhorias.dropna(subset=['data_proposta'])
                    
                    if not df_melhorias.empty:
                        melhorias_por_dia = df_melhorias.groupby(df_melhorias['data_proposta'].dt.date).size()
                        if len(melhorias_por_dia) > 0:
                            dia_mais_melhorias = melhorias_por_dia.idxmax()
                            qtd_mais_melhorias = melhorias_por_dia.max()
                            relatorio += f"• Dia com mais melhorias propostas: {dia_mais_melhorias} ({qtd_mais_melhorias} melhorias)\n"
                            dias_analisados[dia_mais_melhorias] = dias_analisados.get(dia_mais_melhorias, 0) + qtd_mais_melhorias
                except Exception as e:
                    relatorio += f"• Erro na análise de melhorias: {str(e)}\n"
        
        # 🆕 DETERMINAR DIA MAIS PRODUTIVO GERAL
        if dias_analisados:
            dia_mais_produtivo = max(dias_analisados, key=dias_analisados.get)
            relatorio += f"🎯 DIA MAIS PRODUTIVO GERAL: {dia_mais_produtivo} (score: {dias_analisados[dia_mais_produtivo]})\n"
        
        relatorio += "\n"

    # 🆕 ANÁLISE ESPECÍFICA POR TIPO DE PERGUNTA
    if any(palavra in pergunta_lower for palavra in ['qualidade', 'critério', 'template', 'padronização']):
        relatorio += "🎯 ANÁLISE DE QUALIDADE:\n"
        
        if 'documentos' in dados_disponiveis and not dados_disponiveis['documentos'].empty:
            df_docs = dados_disponiveis['documentos']
            if 'critérios_aceite' in df_docs.columns and 'template_padronizado' in df_docs.columns:
                com_criterios = (df_docs['critérios_aceite'] == 'SIM').sum()
                com_template = (df_docs['template_padronizado'] == 'SIM').sum()
                total_docs = len(df_docs)
                
                relatorio += f"• Documentos com critérios de aceite: {com_criterios}/{total_docs} ({com_criterios/total_docs*100:.1f}%)\n"
                relatorio += f"• Documentos com template padronizado: {com_template}/{total_docs} ({com_template/total_docs*100:.1f}%)\n"
                
                # Qualidade por tipo de documento
                if 'tipo_documento' in df_docs.columns:
                    qualidade_por_tipo = df_docs.groupby('tipo_documento').agg({
                        'critérios_aceite': lambda x: (x == 'SIM').sum(),
                        'template_padronizado': lambda x: (x == 'SIM').sum(),
                        'nome_documento': 'count'
                    })
                    relatorio += "• Qualidade por tipo de documento:\n"
                    for tipo in qualidade_por_tipo.index:
                        total = qualidade_por_tipo.loc[tipo, 'nome_documento']
                        criterios = qualidade_por_tipo.loc[tipo, 'critérios_aceite']
                        templates = qualidade_por_tipo.loc[tipo, 'template_padronizado']
                        relatorio += f"  - {tipo}: {criterios}/{total} critérios, {templates}/{total} templates\n"
        
        relatorio += "\n"

    if any(palavra in pergunta_lower for palavra in ['priorização', 'prioridade', 'demandas', 'histórias']):
        relatorio += "📈 ANÁLISE DE PRIORIZAÇÃO DE DEMANDAS:\n"
        
        if 'demandas' in dados_disponiveis and not dados_disponiveis['demandas'].empty:
            df_demandas = dados_disponiveis['demandas']
            if all(col in df_demandas.columns for col in ['total_historias', 'historias_prioridade_definida', 'historias_criterio_aceite']):
                total_historias = df_demandas['total_historias'].sum()
                com_prioridade = df_demandas['historias_prioridade_definida'].sum()
                com_criterio = df_demandas['historias_criterio_aceite'].sum()
                
                relatorio += f"• Total de histórias: {total_historias}\n"
                relatorio += f"• Histórias com prioridade definida: {com_prioridade} ({com_prioridade/total_historias*100:.1f}%)\n"
                relatorio += f"• Histórias com critério de aceite: {com_criterio} ({com_criterio/total_historias*100:.1f}%)\n"
                
                # Evolução temporal
                if 'data_avaliacao' in df_demandas.columns:
                    try:
                        df_temp = df_demandas.copy()
                        df_temp['data_avaliacao'] = pd.to_datetime(df_temp['data_avaliacao'], errors='coerce')
                        df_temp = df_temp.dropna(subset=['data_avaliacao'])
                        df_temp = df_temp.sort_values('data_avaliacao')
                        
                        if len(df_temp) > 1:
                            primeira_avaliacao = df_temp.iloc[0]
                            ultima_avaliacao = df_temp.iloc[-1]
                            
                            taxa_pri_inicial = primeira_avaliacao['historias_prioridade_definida'] / primeira_avaliacao['total_historias'] * 100
                            taxa_pri_final = ultima_avaliacao['historias_prioridade_definida'] / ultima_avaliacao['total_historias'] * 100
                            evolucao_pri = taxa_pri_final - taxa_pri_inicial
                            
                            relatorio += f"• Evolução da priorização: {evolucao_pri:+.1f}% (de {taxa_pri_inicial:.1f}% para {taxa_pri_final:.1f}%)\n"
                    except:
                        pass
        
        relatorio += "\n"

    # ANÁLISE DE MELHORIAS DETALHADA
    if 'melhorias' in dados_disponiveis and not dados_disponiveis['melhorias'].empty:
        df_melhorias = dados_disponiveis['melhorias']
        relatorio += "💡 ANÁLISE DETALHADA DE MELHORIAS:\n"
        relatorio += f"• Total de melhorias: {len(df_melhorias)}\n"
        
        if 'status' in df_melhorias.columns:
            status_counts = df_melhorias['status'].value_counts()
            relatorio += "• Distribuição por status:\n"
            for status, count in status_counts.items():
                percentual = (count / len(df_melhorias)) * 100
                relatorio += f"  - {status}: {count} ({percentual:.1f}%)\n"
        
        if 'impacto' in df_melhorias.columns:
            impacto_counts = df_melhorias['impacto'].value_counts()
            relatorio += "• Impacto das melhorias:\n"
            for impacto, count in impacto_counts.items():
                percentual = (count / len(df_melhorias)) * 100
                relatorio += f"  - {impacto}: {count} ({percentual:.1f}%)\n"
        
        if 'melhoria_aplicada' in df_melhorias.columns:
            aplicadas = len(df_melhorias[df_melhorias['melhoria_aplicada'] == 'SIM'])
            taxa_aplicacao = (aplicadas / len(df_melhorias) * 100) if len(df_melhorias) > 0 else 0
            relatorio += f"• Taxa de aplicação: {taxa_aplicacao:.1f}%\n"
            
            # Tempo médio para aplicação
            if 'data_proposta' in df_melhorias.columns and 'data_aplicacao' in df_melhorias.columns:
                try:
                    df_temp = df_melhorias.copy()
                    df_temp['data_proposta'] = pd.to_datetime(df_temp['data_proposta'], errors='coerce')
                    df_temp['data_aplicacao'] = pd.to_datetime(df_temp['data_aplicacao'], errors='coerce')
                    df_temp = df_temp.dropna(subset=['data_proposta', 'data_aplicacao'])
                    if not df_temp.empty:
                        df_temp['dias_para_aplicar'] = (df_temp['data_aplicacao'] - df_temp['data_proposta']).dt.days
                        tempo_medio_aplicacao = df_temp['dias_para_aplicar'].mean()
                        relatorio += f"• Tempo médio para aplicação: {tempo_medio_aplicacao:.1f} dias\n"
                except:
                    pass
        
        relatorio += "\n"

    # ANÁLISE DE CERIMÔNIAS DETALHADA
    if 'cerimonias' in dados_disponiveis and not dados_disponiveis['cerimonias'].empty:
        df_cerimonias = dados_disponiveis['cerimonias']
        relatorio += "📅 ANÁLISE DETALHADA DE CERIMÔNIAS:\n"
        relatorio += f"• Total de registros: {len(df_cerimonias)}\n"
        
        if 'tipo' in df_cerimonias.columns:
            tipo_counts = df_cerimonias['tipo'].value_counts()
            relatorio += "• Tipos de cerimônias:\n"
            for tipo, count in tipo_counts.items():
                percentual = (count / len(df_cerimonias)) * 100
                relatorio += f"  - {tipo}: {count} ({percentual:.1f}%)\n"
        
        if 'presente' in df_cerimonias.columns:
            presentes = len(df_cerimonias[df_cerimonias['presente'] == 'SIM'])
            taxa_presenca = (presentes / len(df_cerimonias) * 100) if len(df_cerimonias) > 0 else 0
            relatorio += f"• Taxa de presença: {taxa_presenca:.1f}%\n"
        
        if 'duracao_minutos' in df_cerimonias.columns:
            tempo_total = df_cerimonias['duracao_minutos'].sum()
            tempo_medio = tempo_total / len(df_cerimonias) if len(df_cerimonias) > 0 else 0
            relatorio += f"• Tempo total em reuniões: {tempo_total} min ({tempo_total/60:.1f} h)\n"
            relatorio += f"• Duração média: {tempo_medio:.1f} min\n"
            
            # Duração por tipo de cerimônia
            if 'tipo' in df_cerimonias.columns:
                duracao_por_tipo = df_cerimonias.groupby('tipo')['duracao_minutos'].mean().round(1)
                relatorio += "• Duração média por tipo:\n"
                for tipo, duracao in duracao_por_tipo.items():
                    relatorio += f"  - {tipo}: {duracao} min\n"
        
        # Análise de resultados
        if 'resultado' in df_cerimonias.columns:
            resultados_nao_vazios = df_cerimonias[df_cerimonias['resultado'].notna() & (df_cerimonias['resultado'] != '')]
            relatorio += f"• Cerimônias com resultado registrado: {len(resultados_nao_vazios)}/{len(df_cerimonias)}\n"
        
        relatorio += "\n"

    # ANÁLISE DE DOCUMENTOS DETALHADA
    if 'documentos' in dados_disponiveis and not dados_disponiveis['documentos'].empty:
        df_documentos = dados_disponiveis['documentos']
        relatorio += "📋 ANÁLISE DETALHADA DE DOCUMENTAÇÃO:\n"
        relatorio += f"• Total de documentos: {len(df_documentos)}\n"
        
        if 'tipo_documento' in df_documentos.columns:
            tipo_counts = df_documentos['tipo_documento'].value_counts()
            relatorio += "• Tipos de documentos:\n"
            for tipo, count in tipo_counts.items():
                percentual = (count / len(df_documentos)) * 100
                relatorio += f"  - {tipo}: {count} ({percentual:.1f}%)\n"
        
        if 'tempo_minutos' in df_documentos.columns:
            tempo_total = df_documentos['tempo_minutos'].sum()
            tempo_medio = tempo_total / len(df_documentos) if len(df_documentos) > 0 else 0
            relatorio += f"• Tempo total em documentação: {tempo_total} min ({tempo_total/60:.1f} h)\n"
            relatorio += f"• Tempo médio por documento: {tempo_medio:.1f} min\n"
            
            # Tempo por tipo de documento
            if 'tipo_documento' in df_documentos.columns:
                tempo_por_tipo = df_documentos.groupby('tipo_documento')['tempo_minutos'].mean().round(1)
                relatorio += "• Tempo médio por tipo:\n"
                for tipo, tempo in tempo_por_tipo.items():
                    relatorio += f"  - {tipo}: {tempo} min\n"
            
            # Eficiência em documentação
            docs_por_hora = len(df_documentos) / (tempo_total / 60) if tempo_total > 0 else 0
            relatorio += f"• Velocidade de documentação: {docs_por_hora:.1f} documentos/hora\n"
        
        if 'critérios_aceite' in df_documentos.columns:
            com_criterios = len(df_documentos[df_documentos['critérios_aceite'] == 'SIM'])
            taxa_criterios = (com_criterios / len(df_documentos) * 100) if len(df_documentos) > 0 else 0
            relatorio += f"• Documentos com critérios claros: {taxa_criterios:.1f}%\n"
        
        if 'template_padronizado' in df_documentos.columns:
            com_template = len(df_documentos[df_documentos['template_padronizado'] == 'SIM'])
            taxa_template = (com_template / len(df_documentos) * 100) if len(df_documentos) > 0 else 0
            relatorio += f"• Uso de templates: {taxa_template:.1f}%\n"
        
        if 'status' in df_documentos.columns:
            status_counts = df_documentos['status'].value_counts()
            relatorio += "• Status dos documentos:\n"
            for status, count in status_counts.items():
                percentual = (count / len(df_documentos)) * 100
                relatorio += f"  - {status}: {count} ({percentual:.1f}%)\n"
        
        relatorio += "\n"

    # RESUMO EXECUTIVO PARA IA
    relatorio += "\n=== RESUMO EXECUTIVO PARA ANÁLISE IA ===\n"
    
    totais = {}
    for categoria, df in dados_disponiveis.items():
        if not df.empty:
            totais[categoria] = len(df)
    
    relatorio += f"• Volume total de dados: {sum(totais.values())} registros\n"
    for categoria, total in totais.items():
        relatorio += f"• {categoria.title()}: {total} registros\n"
    
    # Métricas chave de performance
    relatorio += "\n📈 MÉTRICAS-CHAVE DE PERFORMANCE:\n"
    
    if 'melhorias' in dados_disponiveis and not dados_disponiveis['melhorias'].empty:
        df_mel = dados_disponiveis['melhorias']
        if 'melhoria_aplicada' in df_mel.columns:
            aplicadas = len(df_mel[df_mel['melhoria_aplicada'] == 'SIM'])
            relatorio += f"• Melhorias aplicadas: {aplicadas}/{len(df_mel)}\n"
    
    if 'cerimonias' in dados_disponiveis and not dados_disponiveis['cerimonias'].empty:
        df_cer = dados_disponiveis['cerimonias']
        if 'presente' in df_cer.columns:
            presentes = len(df_cer[df_cer['presente'] == 'SIM'])
            relatorio += f"• Presença em cerimônias: {presentes}/{len(df_cer)}\n"
    
    if 'documentos' in dados_disponiveis and not dados_disponiveis['documentos'].empty:
        df_doc = dados_disponiveis['documentos']
        if 'critérios_aceite' in df_doc.columns:
            com_criterios = len(df_doc[df_doc['critérios_aceite'] == 'SIM'])
            relatorio += f"• Docs com critérios: {com_criterios}/{len(df_doc)}\n"
    
    return relatorio

def analise_local_po(pergunta, dados_disponiveis, is_fallback_mode=False):
    """
    Fallback para análise local dos dados de PO
    """
    try:
        print(f"🔧 Entrando no fallback local para PO")
        
        # Verificar se há dados
        if not dados_disponiveis or all(df.empty for df in dados_disponiveis.values()):
            return "📭 Não há dados disponíveis para análise com os filtros atuais."
        
        pergunta_lower = pergunta.lower()
        resposta = "📊 **Análise Local - Indicadores de PO:**\n\n"
        
        # RESUMO GERAL
        resposta += "## 📈 Visão Geral do Product Ownership\n\n"
        
        totais = {}
        for categoria, df in dados_disponiveis.items():
            if not df.empty:
                totais[categoria] = len(df)
        
        resposta += f"• **Total de registros:** {sum(totais.values())}\n"
        for categoria, total in totais.items():
            resposta += f"• **{categoria.title()}:** {total} registros\n"
        resposta += "\n"
        
        # ANÁLISE ESPECÍFICA POR CATEGORIA
        if 'melhorias' in dados_disponiveis and not dados_disponiveis['melhorias'].empty:
            df = dados_disponiveis['melhorias']
            resposta += "## 💡 Análise de Melhorias\n"
            resposta += f"• Total de melhorias propostas: {len(df)}\n"
            
            if 'status' in df.columns:
                status_counts = df['status'].value_counts()
                resposta += "• Distribuição por status:\n"
                for status, count in status_counts.head(3).items():
                    resposta += f"  - {status}: {count}\n"
            
            if 'melhoria_aplicada' in df.columns:
                aplicadas = len(df[df['melhoria_aplicada'] == 'SIM'])
                taxa = (aplicadas / len(df) * 100) if len(df) > 0 else 0
                resposta += f"• Taxa de aplicação: {taxa:.1f}%\n"
            resposta += "\n"
        
        if 'cerimonias' in dados_disponiveis and not dados_disponiveis['cerimonias'].empty:
            df = dados_disponiveis['cerimonias']
            resposta += "## 📅 Análise de Cerimônias\n"
            resposta += f"• Total de registros: {len(df)}\n"
            
            if 'tipo' in df.columns:
                tipo_principal = df['tipo'].value_counts().head(1)
                if len(tipo_principal) > 0:
                    resposta += f"• Cerimônia mais frequente: {tipo_principal.index[0]} ({tipo_principal.iloc[0]}x)\n"
            
            if 'presente' in df.columns:
                presentes = len(df[df['presente'] == 'SIM'])
                taxa = (presentes / len(df) * 100) if len(df) > 0 else 0
                resposta += f"• Taxa de presença: {taxa:.1f}%\n"
            
            if 'duracao_minutos' in df.columns:
                tempo_total = df['duracao_minutos'].sum()
                resposta += f"• Tempo total em reuniões: {tempo_total/60:.1f} horas\n"
            resposta += "\n"
        
        if 'demandas' in dados_disponiveis and not dados_disponiveis['demandas'].empty:
            df = dados_disponiveis['demandas']
            resposta += "## 📈 Análise de Demandas\n"
            resposta += f"• Total de avaliações: {len(df)}\n"
            
            if 'total_historias' in df.columns:
                total_historias = df['total_historias'].sum()
                resposta += f"• Histórias avaliadas: {total_historias}\n"
            
            if all(col in df.columns for col in ['total_historias', 'historias_prioridade_definida']):
                priorizadas = df['historias_prioridade_definida'].sum()
                taxa = (priorizadas / total_historias * 100) if total_historias > 0 else 0
                resposta += f"• Taxa de priorização: {taxa:.1f}%\n"
            resposta += "\n"
        
        if 'documentos' in dados_disponiveis and not dados_disponiveis['documentos'].empty:
            df = dados_disponiveis['documentos']
            resposta += "## 📋 Análise de Documentação\n"
            resposta += f"• Total de documentos: {len(df)}\n"
            
            if 'tipo_documento' in df.columns:
                tipo_principal = df['tipo_documento'].value_counts().head(1)
                if len(tipo_principal) > 0:
                    resposta += f"• Tipo mais comum: {tipo_principal.index[0]} ({tipo_principal.iloc[0]}x)\n"
            
            if 'tempo_minutos' in df.columns:
                tempo_medio = df['tempo_minutos'].mean()
                resposta += f"• Tempo médio por documento: {tempo_medio:.1f} min\n"
            
            if 'critérios_aceite' in df.columns:
                com_criterios = len(df[df['critérios_aceite'] == 'SIM'])
                taxa = (com_criterios / len(df) * 100) if len(df) > 0 else 0
                resposta += f"• Docs com critérios claros: {taxa:.1f}%\n"
            resposta += "\n"
        
        # RECOMENDAÇÕES BÁSICAS
        resposta += "## 💡 Recomendações Gerais\n"
        
        if 'melhorias' in dados_disponiveis and not dados_disponiveis['melhorias'].empty:
            df_melhorias = dados_disponiveis['melhorias']
            if 'melhoria_aplicada' in df_melhorias.columns:
                aplicadas = len(df_melhorias[df_melhorias['melhoria_aplicada'] == 'SIM'])
                if aplicadas < len(df_melhorias) * 0.5:
                    resposta += "• **Atenção:** Menos de 50% das melhorias foram aplicadas. Reveja o processo de implementação.\n"
        
        if 'demandas' in dados_disponiveis and not dados_disponiveis['demandas'].empty:
            df_demandas = dados_disponiveis['demandas']
            if all(col in df_demandas.columns for col in ['total_historias', 'historias_prioridade_definida']):
                taxa_prioridade = (df_demandas['historias_prioridade_definida'].sum() / df_demandas['total_historias'].sum() * 100)
                if taxa_prioridade < 80:
                    resposta += f"• **Oportunidade:** Apenas {taxa_prioridade:.1f}% das histórias têm priorização. Melhore este processo.\n"
        
        if is_fallback_mode:
            resposta += "\n🔑 **ERRO DE CONFIGURAÇÃO:** A chave Gemini não foi encontrada. "
            resposta += "Configure a `GEMINI_API_KEY` no seu **secrets.toml** para análises completas com IA."
        
        return resposta
        
    except Exception as e:
        error_msg = f"❌ Erro na análise local: {str(e)}"
        print(error_msg)
        return error_msg
    
# TESTE DA API GEMINI - VERSÃO FINAL CORRIGIDA
def testar_api_gemini():
    """Testa se a API do Gemini está funcionando"""
    print("\n🧪 INICIANDO TESTE DA API GEMINI...")
    
    try:
        # Carrega a chave
        load_dotenv()
        chave = os.getenv('GEMINI_API_KEY')
        
        if not chave:
            print("❌ Chave não encontrada")
            return False
        
        # Configura a API
        genai.configure(api_key=chave)
        print("✅ API configurada")
        
        # 🆕 MODELOS CORRETOS BASEADO NA SUA LISTA:
        modelo = "gemini-2.0-flash"  # Modelo estável e rápido
        
        print(f"🔧 Tentando modelo: {modelo}")
        model = genai.GenerativeModel(modelo)
        print("✅ Modelo carregado")
        
        # Faz uma pergunta simples
        response = model.generate_content("Responda em UMA única palavra: OK")
        print(f"✅ Resposta recebida: {response.text}")
        
        print("🎉 TESTE DA API BEM-SUCEDIDO!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE DA API: {e}")
        return False

# Executa os testes
if __name__ == "__main__":
    testar_api_gemini()