from io import BytesIO
from pathlib import Path

import gower
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import squareform


BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "online_shoppers_intention.csv"
DATA_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00468/online_shoppers_intention.csv"


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH)
    return pd.read_csv(DATA_URL)


@st.cache_data(show_spinner=False)
def prepare_features(df: pd.DataFrame):
    session_navigation_pattern = [
        "Administrative",
        "Informational",
        "ProductRelated",
        "PageValues",
        "OperatingSystems",
        "Browser",
        "TrafficType",
        "VisitorType",
    ]
    temporal_indicators = ["SpecialDay", "Month", "Weekend"]
    numerical = ["ProductRelated", "PageValues", "SpecialDay"]

    df_features = df[session_navigation_pattern + temporal_indicators].copy()
    df_dummies = pd.get_dummies(df_features, drop_first=False)
    categorical_features = df_dummies.drop(columns=numerical).columns.values
    cat_features = [column in categorical_features for column in df_dummies.columns]
    return df_dummies, cat_features


@st.cache_data(show_spinner=False)
def cluster_data(df_model: pd.DataFrame, cat_features: list[bool]):
    dist_gower = gower.gower_matrix(data_x=df_model, cat_features=cat_features)
    gower_vector = squareform(X=dist_gower, force="tovector")
    return linkage(y=gower_vector, method="complete")


def to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="agrupamentos")
    return output.getvalue()


def inject_style():
    st.markdown(
        """
        <style>
        .stApp {
            background: #090d14;
            color: #f7f9fc;
        }
        [data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid #253041;
        }
        [data-testid="stHeader"] {
            background: rgba(9, 13, 20, .92);
        }
        div[data-testid="stMetric"] {
            background: #111827;
            border: 1px solid #253041;
            border-radius: 8px;
            padding: 14px;
        }
        .hero {
            background: linear-gradient(135deg, #111827 0%, #0f766e 100%);
            border-left: 6px solid #22c55e;
            border-radius: 8px;
            padding: 28px 32px;
            margin-bottom: 24px;
        }
        .hero h1 {
            margin: 0 0 10px 0;
            color: #fff;
        }
        .hero p {
            margin: 4px 0;
            color: #dbeafe;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def plot_revenue_count(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.countplot(data=df, x="Revenue", ax=ax, palette=["#0f766e", "#2563eb"])
    ax.set_title("Distribuicao da variavel Revenue")
    ax.set_xlabel("Houve compra")
    ax.set_ylabel("Sessoes")
    st.pyplot(fig, use_container_width=True)


def plot_correlation(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.heatmap(df.corr(numeric_only=True), cmap="viridis", ax=ax)
    ax.set_title("Correlacao entre variaveis numericas")
    st.pyplot(fig, use_container_width=True)


def plot_dendrogram(z_matrix, groups: int, threshold: float):
    fig, ax = plt.subplots(figsize=(14, 5))
    dendrogram(
        Z=z_matrix,
        p=6,
        truncate_mode="level",
        color_threshold=threshold,
        show_leaf_counts=True,
        leaf_font_size=8,
        leaf_rotation=45,
        show_contracted=True,
        ax=ax,
    )
    ax.set_title(f"Dendrograma hierarquico - {groups} grupos")
    ax.set_ylabel("Distancia")
    ax.set_xticks([])
    st.pyplot(fig, use_container_width=True)


def main():
    st.set_page_config(
        page_title="Agrupamento Hierarquico | Weslei Granza",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_style()

    st.markdown(
        """
        <div class="hero">
            <h1>Projeto de Agrupamento Hierarquico</h1>
            <p><strong>Por:</strong> Weslei Granza | <strong>Data:</strong> 28 de maio de 2026</p>
            <p>Analise de sessoes de e-commerce com agrupamento hierarquico e distancia de Gower.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("Configuracao")
    st.sidebar.caption("A base usada e o arquivo online_shoppers_intention.csv incluido no projeto.")

    df = load_data()
    max_rows = min(len(df), 2500)
    sample_size = st.sidebar.slider(
        "Registros para processar",
        min_value=300,
        max_value=max_rows,
        value=min(1200, max_rows),
        step=100,
        help="A matriz Gower cresce rapidamente. No Render free, use uma amostra para manter o app estavel.",
    )
    random_state = st.sidebar.number_input("Semente da amostra", min_value=1, max_value=9999, value=42)

    df_sample = df.sample(n=sample_size, random_state=int(random_state)).reset_index(drop=True)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Linhas da base", f"{len(df):,}".replace(",", "."))
    metric_cols[1].metric("Linhas analisadas", f"{len(df_sample):,}".replace(",", "."))
    metric_cols[2].metric("Colunas", df.shape[1])
    metric_cols[3].metric("Taxa de compra", f"{df_sample['Revenue'].mean() * 100:.1f}%")

    st.divider()
    st.subheader("Base de dados")
    st.write(
        "A base Online Shoppers Purchase Intention registra sessoes de navegacao em e-commerce. "
        "O objetivo e verificar se padroes de navegacao diferentes formam grupos com propensao de compra distinta."
    )
    st.dataframe(df_sample.head(30), use_container_width=True)

    tab_overview, tab_cluster, tab_results = st.tabs(["Exploracao", "Agrupamento", "Resultados"])

    with tab_overview:
        col1, col2 = st.columns(2)
        with col1:
            plot_revenue_count(df_sample)
        with col2:
            plot_correlation(df_sample)

        st.write("Resumo estatistico")
        st.dataframe(df_sample.describe(), use_container_width=True)

    with tab_cluster:
        st.info("Calculando a matriz de Gower e o agrupamento hierarquico para a amostra selecionada.")
        df_model, cat_features = prepare_features(df_sample)
        z_matrix = cluster_data(df_model, cat_features)

        col1, col2 = st.columns(2)
        with col1:
            plot_dendrogram(z_matrix, groups=3, threshold=0.53)
        with col2:
            plot_dendrogram(z_matrix, groups=4, threshold=0.50)

        st.write("Primeiras linhas da matriz de ligacao")
        st.dataframe(
            pd.DataFrame(z_matrix, columns=["id1", "id2", "dist", "n"]).head(20),
            use_container_width=True,
        )

    with tab_results:
        df_result = df_sample.copy()
        df_result["grupo_3"] = fcluster(z_matrix, t=3, criterion="maxclust")
        df_result["grupo_4"] = fcluster(z_matrix, t=4, criterion="maxclust")

        col1, col2 = st.columns(2)
        with col1:
            st.write("Quantidade por grupo - 3 grupos")
            st.dataframe(df_result["grupo_3"].value_counts().sort_index().rename("quantidade"))
        with col2:
            st.write("Quantidade por grupo - 4 grupos")
            st.dataframe(df_result["grupo_4"].value_counts().sort_index().rename("quantidade"))

        st.write("Compra por grupo - 3 grupos")
        st.dataframe(
            pd.crosstab(df_result["grupo_3"], df_result["Revenue"], normalize="index")
            .mul(100)
            .round(2),
            use_container_width=True,
        )

        st.write("Compra por grupo - 4 grupos")
        st.dataframe(
            pd.crosstab(df_result["grupo_4"], df_result["Revenue"], normalize="index")
            .mul(100)
            .round(2),
            use_container_width=True,
        )

        st.subheader("Conclusao")
        st.write(
            "Os agrupamentos mostram que diferentes perfis de navegacao apresentam participacoes distintas "
            "de sessoes com compra. Essa separacao ajuda a identificar grupos prioritarios para acoes de "
            "marketing, melhoria de experiencia e analises mais direcionadas do funil de conversao."
        )

        st.download_button(
            "Baixar resultados em Excel",
            data=to_excel(df_result),
            file_name="agrupamento_hierarquico_weslei_granza.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
