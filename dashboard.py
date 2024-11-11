import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
from globals import *

st.set_page_config(page_title="Visualização de Dados", layout="wide")

def carregar_dados():
    """carregar dados do banco """
    with sqlite3.connect(BANCO_DADOS) as conn:
        query = "SELECT * FROM registros"  # Nome correto da tabela
        df = pd.read_sql_query(query, conn)
        return df
    return None

# Exibir detalhes de um registro selecionado
def exibir_detalhes(linha):
    """ exibir detalhes """
    st.subheader("Detalhes do Registro")
    for coluna, valor in linha.items():
        st.write(f"**{coluna}**: {valor}")

# Interface principal
def main():
    """ principal """
    st.title("Sistema de Concessão de Benefícios da Mútua")

    # Carregar os dados do banco
    df = carregar_dados()

    # Filtrar as colunas relevantes 
    df_filtrado = df[["nome", "risco", "renda_mensal","credito_solicitado"]]

    # Destacar toda a linha com situação "crítica" em vermelho
    def colorir_linhas(row):
        if row["risco"] == "alto":
            return ["background-color: red; color: white;" for _ in row]
        if row["risco"] == "moderado":
            return ["background-color: yellow; color: black;" for _ in row]
        if row["risco"] == "baixo":
            return ["background-color: green; color: black;" for _ in row]
        
        return [""] * len(row)

    # Aplicar estilos de coloração nas linhas
    st.subheader("Tabela de Dados")
    styled_df = df_filtrado.style.apply(colorir_linhas, axis=1)

    # Usar `st.table()` para garantir exibição completa dos dados filtrados
    st.table(styled_df)

    # Permitir seleção de um registro para ver detalhes
    indice = st.text_input("Informe o índice da linha para visualizar detalhes:")
    if indice.isdigit() and int(indice) < len(df_filtrado):
        linha = df.iloc[int(indice)].to_dict()  # Obter linha completa
        exibir_detalhes(linha)
    elif indice:
        st.warning("Índice inválido. Informe um número válido.")

    # Gerar gráfico de barras com a totalização por risco
    st.subheader("Gráfico de Barras - Totalização por Risco")
    grafico_df = df["risco"].value_counts().reset_index()
    grafico_df.columns = ["risco", "Total"]

    grafico = alt.Chart(grafico_df).mark_bar().encode(
        x="risco",
        y="Total",
        color="risco"
    ).properties(
        width=800,
        height=400
    )

    st.altair_chart(grafico)

if __name__ == "__main__":
    main()
