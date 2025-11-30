import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard Corporativo", layout="wide", initial_sidebar_state="expanded")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['estoque_db']
collection = db['produtos']

st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #D32F2F;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #555;
    }
    div[data-testid="stMetric"] {
        background-color: #fff5f5;
        border: 1px solid #ffcdd2;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("Gestão de Inventário")
    menu = st.radio(
        "Navegação", 
        ["Dashboard Geral", "Cadastrar Item", "Editar/Excluir"],
    )

dados = list(collection.find({}, {"_id": 0}))
df = pd.DataFrame(dados)

if menu == "Dashboard Geral":
    st.subheader("Inventário")

    if not df.empty:
        total_itens = df['quantidade'].sum()
        valor_total = (df['quantidade'] * df['preco']).sum()
        total_categorias = len(df['categoria'].unique())

        c1, c2, c3 = st.columns(3)
        c1.metric("Processos (Itens Totais)", f"{int(total_itens)}")
        c2.metric("Valor Acumulado", f"R$ {valor_total:,.2f}")
        c3.metric("Categorias Ativas", f"{total_categorias}")

        st.markdown("---")

        col_left, col_right = st.columns([1.5, 1])

        with col_left:
            st.markdown("##### Relator atual (Itens por Produto)")
            df_sorted = df.sort_values(by="quantidade", ascending=True).tail(10)
            
            fig_bar = px.bar(
                df_sorted, 
                x="quantidade", 
                y="nome", 
                orientation='h',
                text="quantidade",
                color_discrete_sequence=["#D32F2F"]
            )
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_visible=False,
                yaxis_title=None,
                margin=dict(l=0, r=0, t=0, b=0),
                height=350
            )
            fig_bar.update_traces(textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            st.markdown("##### Classe processual (Por Categoria)")
            df_cat = df.groupby("categoria")["quantidade"].sum().reset_index()
            
            fig_donut = px.pie(
                df_cat, 
                values="quantidade", 
                names="categoria", 
                hole=0.6,
                color_discrete_sequence=["#8b0000", "#c62828", "#e53935", "#ef5350", "#ffcdd2"]
            )
            fig_donut.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=350,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            fig_donut.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_donut, use_container_width=True)
            
        st.markdown("---")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Baixar Relatório em CSV",
            data=csv,
            file_name="relatorio_estoque.csv",
            mime="text/csv",
            type="primary" 
        )

    else:
        st.info("Nenhum dado no acervo.")

elif menu == "Cadastrar Item":
    st.header("Novo Cadastro")
    nome = st.text_input("Nome do Produto")
    categoria = st.selectbox("Categoria", ["Eletrônicos", "Móveis", "Vestuário", "Alimentos", "Outros"])
    quantidade = st.number_input("Quantidade", min_value=0, step=1)
    preco = st.number_input("Preço Unitário (R$)", min_value=0.0, format="%.2f")
    
    if st.button("Cadastrar"):
        if nome:
            if collection.find_one({"nome": nome}):
                st.warning("Item já existe.")
            else:
                collection.insert_one({
                    "nome": nome,
                    "categoria": categoria,
                    "quantidade": quantidade,
                    "preco": preco
                })
                st.success("Registrado com sucesso!")

elif menu == "Editar/Excluir":
    st.header("Gestão de Registros")
    if not df.empty:
        produto_sel = st.selectbox("Selecione o Item", df['nome'].unique())
        item_atual = df[df['nome'] == produto_sel].iloc[0]
        
        col_a, col_b = st.columns(2)
        nova_qtd = col_a.number_input("Nova Quantidade", min_value=0, value=int(item_atual['quantidade']))
        novo_preco = col_b.number_input("Novo Preço", min_value=0.0, value=float(item_atual['preco']))
        
        c1, c2 = st.columns([1,1])
        if c1.button("Atualizar Dados"):
            collection.update_one({"nome": produto_sel}, {"$set": {"quantidade": nova_qtd, "preco": novo_preco}})
            st.success("Atualizado!")
            st.rerun()
            
        if c2.button("Excluir Definitivamente"):
            collection.delete_one({"nome": produto_sel})
            st.warning("Excluído.")
            st.rerun()
