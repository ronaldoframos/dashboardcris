from globals import *

import sqlite3
import pandas as pd                 # type: ignore
import altair as alt                # type: ignore
from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel             # type: ignore
from threading import Thread        # type: ignore
import uvicorn                      # type: ignore


app = FastAPI()

st.set_page_config(page_title="Visualização de Dados", layout="wide")

# Modelo para o registro que será enviado via API
class Registro(BaseModel):
    nome: str
    risco: str
    renda_mensal: float
    credito_solicitado: float

def carregar_dados():
    """Carregar dados do banco de dados"""
    with sqlite3.connect(BANCO_DADOS) as conn:
        query = "SELECT * FROM registros"
        df = pd.read_sql_query(query, conn)
    return df

# Rota para adicionar um novo registro
@app.post("/registros/")
async def adicionar_registro(registro: Registro):
    try:
        with sqlite3.connect(BANCO_DADOS) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO registros (nome, risco, renda_mensal, credito_solicitado) VALUES (?, ?, ?, ?)",
                (registro.nome, registro.risco, registro.renda_mensal, registro.credito_solicitado)
            )
            conn.commit()
        return {"mensagem": "Registro adicionado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao adicionar registro: {e}")

# Função para exibir detalhes de um registro selecionado
def exibir_detalhes(linha):
    st.subheader("Detalhes do Registro")
    for coluna, valor in linha.items():
        st.write(f"**{coluna}**: {valor}")

# Função principal para exibição no Streamlit
def main():
    st.title("Sistema de Concessão de Benefícios da Mútua")

    # Carregar os dados do banco
    df = carregar_dados()

    # Filtrar as colunas relevantes 
    df_filtrado = df[["nome", "risco", "renda_mensal","credito_solicitado"]]

    # Função de coloração das linhas
    def colorir_linhas(row):
        if row["risco"] == "alto":
            return ["background-color: red; color: white;" for _ in row]
        elif row["risco"] == "moderado":
            return ["background-color: yellow; color: black;" for _ in row]
        elif row["risco"] == "baixo":
            return ["background-color: green; color: black;" for _ in row]
        return [""] * len(row)

    # Aplicar estilos de coloração nas linhas
    st.subheader("Tabela de Dados")
    styled_df = df_filtrado.style.apply(colorir_linhas, axis=1)
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

# Função para rodar o FastAPI em um thread separado
def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Rodar a API e o Streamlit simultaneamente
if __name__ == "__main__":
    api_thread = Thread(target=start_api, daemon=True)
    api_thread.start()
    main()
