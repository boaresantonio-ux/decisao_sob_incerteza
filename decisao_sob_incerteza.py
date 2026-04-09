
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from fpdf import FPDF
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
        edited_df = st.data_editor(df_input, use_container_width=True)
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
    edited_df = st.data_editor(df_vazio, use_container_width=True)

# --- Parâmetros de Cálculo ---
with st.sidebar:
    st.divider()
    alpha = st.slider("Coeficiente de Hurwicz (α)", 0.0, 1.0, 0.5)

# --- Processamento ---
if st.button("Gerar Análise Completa"):
    matriz = edited_df.values
    
    # Cálculos
    resultados = {
        'Maximax (Otimista)': edited_df.max(axis=1),
        'Wald (Pessimista)': edited_df.min(axis=1),
        'Laplace': edited_df.mean(axis=1),
        'Hurwicz': (alpha * edited_df.max(axis=1)) + ((1 - alpha) * edited_df.min(axis=1))
    }
    
    # Savage (Arrependimento)
    max_colunas = matriz.max(axis=0)
    matriz_regret = max_colunas - matriz
    resultados['Savage (Arrependimento)'] = matriz_regret.max(axis=1)
    
    df_res = pd.DataFrame(resultados)

    st.subheader("RESULTADO DA MATRIZ DE DECISÃO")
    st.dataframe(df_res.style.highlight_max(axis=0, subset=df_res.columns[:-1]).highlight_min(axis=0, subset=['Savage (Arrependimento)']))

    # Gráficos
    col1, col2 = st.columns(2)

    # Definindo as cores
    cores_map = {
    'Maximax (Otimista)': '#2ecc71',      # Verde
    'Wald (Pessimista)': '#e74c3c',      # Vermelho
    'Laplace': '#3498db',                # Azul
    'Hurwicz': '#9b59b6',                # Roxo
    'Savage (Arrependimento)': '#f1c40f'  # Amarelo
}
    
    with col1:
        st.subheader("Comparação de Ganhos")
        fig_ganhos = go.Figure()
        for c in cores_map.keys():
            if c in df_res.columns:
                fig_ganhos.add_trace(go.Bar(
                    name=c, 
                    x=df_res.index, 
                    y=df_res[c],
                    marker_color=cores_map[c] # Força a cor definida
                ))
        # for c in ['Maximax (Otimista)', 'Wald (Pessimista)', 'Laplace', 'Hurwicz', 'Savage (Arrependimento)', ]:
        #     fig_ganhos.add_trace(go.Bar(name=c, x=df_res.index, y=df_res[c]))
        fig_ganhos.update_layout(barmode='group', autosize=True, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0))
        st.plotly_chart(fig_ganhos, use_container_width=True, width=1080)

    # with col2:
    #     st.subheader("Arrependimento (Savage)")
    #     fig_sav = go.Figure(go.Bar(x=df_res.index, y=df_res['Savage (Arrependimento)'], marker_color='red'))
    #     fig_sav.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    #     st.plotly_chart(fig_sav, use_container_width=True)

# --- Função de PDF Corrigida ---
    def gerar_pdf_completo(res, fig):
        pdf = FPDF()
        pdf.add_page()
        
        # Título
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "Relatorio de Analise de Decisao", ln=True, align='C')
        pdf.ln(5)
        
        # Tabela de Resultados
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, "Tabela de Resultados:", ln=True)
        pdf.set_font("Arial", size=9)
        
        largura_col = 190 / (len(res.columns) + 1)
        pdf.cell(largura_col, 10, "Acao", border=1)
        for col in res.columns:
            pdf.cell(largura_col, 10, col[:10], border=1)
        pdf.ln()
        
        for i in range(len(res)):
            pdf.cell(largura_col, 10, str(res.index[i]), border=1)
            for val in res.iloc[i]:
                pdf.cell(largura_col, 10, f"{val:.2f}", border=1)
            pdf.ln()
            
        pdf.ln(5)

        # --- Inserir Gráfico e Atualizar Posição Y ---
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_tmp:
            fig.write_image(img_tmp.name, engine="kaleido", width=1000, height=600)
            img_path = img_tmp.name
            
            # Captura a posição Y atual, insere a imagem e move o Y manualmente
            y_atual = pdf.get_y()
            pdf.image(img_path, x=10, y=y_atual, w=180)
            
            # Move o cursor para baixo (altura proporcional à largura de 180w)
            # 600 height / 1000 width * 180w = 108mm de altura aproximadamente
            pdf.set_y(y_atual + 115) 

        # --- Resumo de Vencedores (Agora abaixo do gráfico) ---
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, "Resumo das Melhores Opcoes:", ln=True)
        pdf.set_font("Arial", size=11)
        
        for crit in res.columns:
            vencedor = res[crit].idxmin() if "Savage" in crit else res[crit].idxmax()
            pdf.cell(190, 8, f"- {crit}: {vencedor}", ln=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            pdf_path = tmp_pdf.name
            
        return pdf_path, img_path
    
    # --- Execução do PDF ---
    try:
        pdf_file, temp_img = gerar_pdf_completo(df_res, fig_ganhos)
        
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="⬇️ Baixar Relatório Completo (PDF)",
                data=f,
                file_name="relatorio_matriz_decisao.pdf",
                mime="application/pdf"
            )
        
        # Limpar arquivos temporários
        os.remove(pdf_file)
        os.remove(temp_img)
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}. Certifique-se de ter 'kaleido' instalado (pip install kaleido).")