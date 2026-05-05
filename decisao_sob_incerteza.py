
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import tempfile
import os

st.set_page_config(page_title="Decisão sob Incerteza1", layout="wide")

st.title("📊 MATRIZ DE DECISÃO")

# --- Opções de Entrada ---
metodo_entrada = st.radio("Escolha como deseja inserir os dados:", ("Digitação Manual", "Upload de Arquivo (CSV/Excel)"))

if metodo_entrada == "Upload de Arquivo (CSV/Excel)":
    uploaded_file = st.file_uploader("Arraste seu arquivo aqui", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df_input = pd.read_csv(uploaded_file, index_col=0)
        else:
            df_input = pd.read_excel(uploaded_file, index_col=0)
        
        st.write("Visualização dos dados carregados:")
        edited_df = st.data_editor(df_input, width="stritch")
    else:
        st.info("Aguardando arquivo... Certifique-se de que a primeira coluna contenha os nomes das Ações.")
        st.stop()

else:
    # --- Configuração Manual (Lateral) ---
    with st.sidebar:
        st.header("Dimensões da Matriz")
        n_acoes = st.number_input("Número de Ações", min_value=1, value=3)
        n_estados = st.number_input("Estados da Natureza", min_value=1, value=3)
    
    colunas = [f"E{i+1}" for i in range(n_estados)]
    indices = [f"Ação {i+1}" for i in range(n_acoes)]
    
    df_vazio = pd.DataFrame(0.0, index=indices, columns=colunas)
    
    st.subheader("Preencha a Matriz Abaixo")
    edited_df = st.data_editor(df_vazio, width="stretch")

# --- Parâmetros de Cálculo ---
with st.sidebar:
    st.divider()
    alpha = st.slider("Coeficiente de Hurwicz (α)", 0.0, 1.0, 0.5)

# --- Processamento ---
# Inicializa o estado se não existir
if 'analise_feita' not in st.session_state:
    st.session_state.analise_feita = False

if st.button("Gerar Análise Completa"):
    st.session_state.analise_feita = True

# Tudo o que depende do botão agora depende do estado da sessão
if st.session_state.analise_feita:
    matriz = edited_df.values
    
    # 1. Cálculos Básicos
    resultados = {
        'Maximax (Otimista)': edited_df.max(axis=1),
        'Wald (Pessimista)': edited_df.min(axis=1),
        'Laplace': edited_df.mean(axis=1),
    }
    
    # 2. Hurwicz (Calculado aqui para ser reativo ao slider MESMO após o botão ser clicado)
    hurwicz_data = (alpha * edited_df.max(axis=1)) + ((1 - alpha) * edited_df.min(axis=1))
    resultados['Hurwicz'] = hurwicz_data
    
    # 3. Savage (Arrependimento)
    max_colunas = matriz.max(axis=0)
    matriz_regret = max_colunas - matriz
    resultados['Savage (Arrependimento)'] = matriz_regret.max(axis=1)
    
    df_res = pd.DataFrame(resultados)

    # --- Tabela de Resultados ---
    st.subheader("RESULTADO DA MATRIZ DE DECISÃO")
    st.dataframe(df_res.style.highlight_max(axis=0, subset=['Maximax (Otimista)', 'Wald (Pessimista)', 'Laplace', 'Hurwicz'])
                 .highlight_min(axis=0, subset=['Savage (Arrependimento)']))

    # --- Outros Gráficos ---
    col1, col2 = st.columns(2)
    cores_map = {
        'Maximax (Otimista)': '#2ecc71',
        'Wald (Pessimista)': '#e74c3c',
        'Laplace': '#3498db',
        'Hurwicz': '#9b59b6',
        'Savage (Arrependimento)': '#f1c40f'
    }
    
    
    st.subheader("Comparação de Todos os Critérios")
    fig_ganhos = go.Figure()
    for c, cor in cores_map.items():
        if c in df_res.columns:
            fig_ganhos.add_trace(go.Bar(name=c, x=df_res.index, y=df_res[c], marker_color=cor))
    fig_ganhos.update_layout(barmode='group', autosize=True, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    st.plotly_chart(fig_ganhos, width='stretch')


    # Seção Gráfico de Radar
    st.subheader("Perfil Decisório (Gráfico de Radar)")
    # Definindo os critérios para os eixos do radar
    categorias = ['Maximax (Otimista)', 'Wald (Pessimista)', 'Laplace', 'Hurwicz']

    fig_radar = go.Figure()

    for acao in df_res.index:
        fig_radar.add_trace(go.Scatterpolar(
            r=[df_res.loc[acao, c] for c in categorias],
            theta=categorias,
            fill='toself',
            name=acao
        ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[df_res[categorias].values.min(), df_res[categorias].values.max()]
            )),
        showlegend=True,
        height=500
    )

    st.plotly_chart(fig_radar, use_container_width=True)

    # Seção do Gráfico de Hurwicz
    st.divider()
    st.subheader(f"📈 Critério de Hurwicz Dinâmico (α = {alpha})")
    fig_hur = go.Figure()
    fig_hur.add_trace(go.Bar(
        x=df_res.index,
        y=df_res['Hurwicz'],
        marker_color='#9b59b6',
        text=df_res['Hurwicz'].round(2),
        textposition='auto',
    ))
    fig_hur.update_layout(template="plotly_white", height=350)
    st.plotly_chart(fig_hur, width='stretch')


    # Seção do Grafico de linha sensitiva
    st.subheader(f"Grafico de linha sensitiva")
    alphas = np.linspace(0, 1, 100)
    fig_sens = go.Figure()

    for acao in edited_df.index:
        melhor = edited_df.loc[acao].max()
        pior = edited_df.loc[acao].min()
        # Calculando a reta: y = alpha*max + (1-alpha)*min
        y_vals = [a * melhor + (1 - a) * pior for a in alphas]
        
        fig_sens.add_trace(go.Scatter(x=alphas, y=y_vals, mode='lines', name=acao))

    fig_sens.update_layout(
        xaxis_title="Coeficiente de Otimismo (α)",
        yaxis_title="Valor Esperado",
        hovermode="x unified"
    )
    st.plotly_chart(fig_sens, width="stretch")


    # Composição do Valor de Hurwicz
    st.subheader("Composição do Valor de Hurwicz (Pessimismo vs. Otimismo)")
    pessimismo_part = (1 - alpha) * edited_df.min(axis=1)
    otimismo_part = alpha * edited_df.max(axis=1)

    fig_empilhado = go.Figure()

    # Adiciona a base (Pessimismo)
    fig_empilhado.add_trace(go.Bar(
        name='Peso do Pessimismo (Segurança)',
        x=edited_df.index,
        y=pessimismo_part,
        marker_color='#e74c3c' # Vermelho
    ))

    # Adiciona o topo (Otimismo)
    fig_empilhado.add_trace(go.Bar(
        name='Peso do Otimismo (Oportunidade)',
        x=edited_df.index,
        y=otimismo_part,
        marker_color='#2ecc71' # Verde
    ))

    fig_empilhado.update_layout(
        barmode='stack',
        yaxis_title="Valor de Hurwicz Total",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=450
    )

    st.plotly_chart(fig_empilhado, use_container_width=True)
   

# --- Função de PDF Corrigida ---
    def gerar_pdf_completo(res, fig_geral, fig_radar, fig_hur, fig_sens, fig_emp, alpha_val):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # --- Cabeçalho ---
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "Relatorio de Apoio ao Censo - Analise de Decisao", ln=1, align='C')
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(190, 8, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Alfa: {alpha_val}", ln=1, align='C')
        pdf.ln(5)
        
        # --- Tabela de Resultados ---
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, "1. Matriz de Resultados:", ln=1)
        pdf.set_font("Arial", size=8)
        
        largura_col = 190 / (len(res.columns) + 1)
        pdf.cell(largura_col, 10, "Acao", border=1, align='C')
        for col in res.columns:
            pdf.cell(largura_col, 10, str(col)[:10], border=1, align='C')
        pdf.ln()
        
        for i in range(len(res)):
            pdf.cell(largura_col, 10, str(res.index[i]), border=1)
            for val in res.iloc[i]:
                pdf.cell(largura_col, 10, "{:.2f}".format(val), border=1, align='C')
            pdf.ln()

        # Lista para gerenciar as imagens temporárias
        temp_imgs = []

        def add_chart_to_pdf(pdf, fig, title, w=180, h=450):
            if pdf.get_y() > 180: # Nova página se não couber
                pdf.add_page()
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 10, title, ln=1)
            
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            fig.write_image(tmp.name, width=1000, height=h)
            temp_imgs.append(tmp.name)
            pdf.image(tmp.name, x=15, w=170)
            pdf.ln(5)

        # --- Inserindo os 5 Gráficos ---
        add_chart_to_pdf(pdf, fig_geral, "2. Comparativo de Todos os Criterios")
        add_chart_to_pdf(pdf, fig_radar, "3. Perfil Decisorio (Radar)", h=600)
        add_chart_to_pdf(pdf, fig_hur, "4. Detalhamento Hurwicz (Barras)")
        add_chart_to_pdf(pdf, fig_sens, "5. Analise de Sensibilidade (Alfa 0 a 1)")
        add_chart_to_pdf(pdf, fig_emp, "6. Composicao do Valor (Pessimismo vs Otimismo)")

        # --- Vencedores ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, "Conclusao e Melhores Estrategias:", ln=1)
        pdf.set_font("Arial", '', 11)
        for crit in res.columns:
            vencedor = res[crit].idxmin() if "Savage" in crit else res[crit].idxmax()
            pdf.cell(190, 8, f"- Para o criterio {crit}, a melhor acao e: {vencedor}", ln=1)

        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp_pdf.name)
        return tmp_pdf.name, temp_imgs
    
   # --- Execução do PDF ---
    try:
        # Passamos todas as 5 figuras geradas no código
        pdf_path, temp_images = gerar_pdf_completo(
            df_res, 
            fig_ganhos, 
            fig_radar, 
            fig_hur, 
            fig_sens, 
            fig_empilhado, 
            alpha
        )
        
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
        st.download_button(
            label="⬇️ Baixar Relatório do Censo (PDF)",
            data=pdf_bytes,
            file_name=f"relatorio_censo_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            key="btn_pdf_final"
        )
        
        # Limpeza
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        for img in temp_images:
            if os.path.exists(img):
                os.remove(img)
                    
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")