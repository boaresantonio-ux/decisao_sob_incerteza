# 📊 Matriz de Decisão sob Incerteza

Uma aplicação interativa desenvolvida com **Streamlit** para auxiliar na tomada de decisão estratégica utilizando critérios clássicos de incerteza (Maximax, Wald, Laplace, Hurwicz e Savage).

## 🚀 Funcionalidades

- **Entrada de Dados Flexível**: Digitação manual diretamente na interface ou upload de arquivos CSV/Excel.
- **Critérios de Análise**:
  - **Maximax**: Abordagem otimista.
  - **Wald (Maximin)**: Abordagem pessimista/conservadora.
  - **Laplace**: Baseado na equiprobabilidade.
  - **Hurwicz**: Balanço entre otimismo e pessimismo (alfa ajustável).
  - **Savage**: Minimização do arrependimento máximo.
- **Visualização Avançada**: Gráficos de Radar (Perfil Decisório), Análise de Sensibilidade e Composição de Valor.
- **Exportação**: Geração de relatório completo em PDF com tabelas e gráficos.

## 🛠️ Tecnologias Utilizadas

* [Python](https://www.python.org/) - Linguagem base.
* [Streamlit](https://streamlit.io/) - Framework para a interface web.
* [Pandas/Numpy](https://pandas.pydata.org/) - Processamento de dados.
* [Plotly](https://plotly.com/python/) - Gráficos interativos.
* [FPDF2](https://pyfpdf.github.io/fpdf2/) - Geração de relatórios PDF.
* [Kaleido](https://pypi.org/project/kaleido/) - Exportação de imagens estáticas para o PDF.

## 📋 Pré-requisitos

Antes de começar, você precisará ter instalado em sua máquina:
- Python 3.8 ou superior.
- Pip (Gerenciador de pacotes do Python).

## 🔧 Instalação

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/nome-do-repositorio.git](https://github.com/boaresantonio-ux/decisao_sob_incerteza.git)
   
   cd decisao_sob_incerteza
   
   pip install -r requirements.txt
   
   streamlit run app.py

# 🤝 Contribuição
Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request.

Desenvolvido por Boares António