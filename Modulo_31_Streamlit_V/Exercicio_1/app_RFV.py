from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).parent
DEMO_FILE = BASE_DIR / "input" / "dados.csv"


@st.cache_data
def load_demo_data() -> pd.DataFrame:
    return pd.read_csv(DEMO_FILE, parse_dates=["DiaCompra"])


@st.cache_data
def load_uploaded_data(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.lower().endswith(".xlsx"):
        return pd.read_excel(uploaded_file, parse_dates=["DiaCompra"])
    return pd.read_csv(uploaded_file, parse_dates=["DiaCompra"])


@st.cache_data
def to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=True, sheet_name="RFV")
    return output.getvalue()


def recencia_class(x, r, q_dict):
    """Na recencia, quanto menor o quartil, melhor o cliente."""
    if x <= q_dict[r][0.25]:
        return "A"
    if x <= q_dict[r][0.50]:
        return "B"
    if x <= q_dict[r][0.75]:
        return "C"
    return "D"


def freq_val_class(x, fv, q_dict):
    """Na frequencia e no valor, quanto maior o quartil, melhor o cliente."""
    if x <= q_dict[fv][0.25]:
        return "D"
    if x <= q_dict[fv][0.50]:
        return "C"
    if x <= q_dict[fv][0.75]:
        return "B"
    return "A"


def inject_style():
    st.markdown(
        """
        <style>
        .stApp {
            background: #090d14;
            color: #f5f7fb;
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
            padding: 16px;
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
            color: #ffffff;
            font-size: 2.2rem;
        }
        .hero p {
            margin: 4px 0;
            color: #dbeafe;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def build_rfv(df_compras: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp]:
    required_columns = {"ID_cliente", "DiaCompra", "CodigoCompra", "ValorTotal"}
    missing = required_columns.difference(df_compras.columns)
    if missing:
        raise ValueError(f"Colunas obrigatorias ausentes: {', '.join(sorted(missing))}")

    df_compras = df_compras.copy()
    df_compras["DiaCompra"] = pd.to_datetime(df_compras["DiaCompra"])
    dia_atual = df_compras["DiaCompra"].max()

    df_recencia = df_compras.groupby("ID_cliente", as_index=False)["DiaCompra"].max()
    df_recencia.columns = ["ID_cliente", "DiaUltimaCompra"]
    df_recencia["Recencia"] = df_recencia["DiaUltimaCompra"].apply(lambda x: (dia_atual - x).days)
    df_recencia.drop("DiaUltimaCompra", axis=1, inplace=True)

    df_frequencia = (
        df_compras[["ID_cliente", "CodigoCompra"]]
        .groupby("ID_cliente")
        .count()
        .reset_index()
    )
    df_frequencia.columns = ["ID_cliente", "Frequencia"]

    df_valor = (
        df_compras[["ID_cliente", "ValorTotal"]]
        .groupby("ID_cliente")
        .sum()
        .reset_index()
    )
    df_valor.columns = ["ID_cliente", "Valor"]

    df_rfv = (
        df_recencia.merge(df_frequencia, on="ID_cliente")
        .merge(df_valor, on="ID_cliente")
        .set_index("ID_cliente")
    )

    quartis = df_rfv.quantile(q=[0.25, 0.50, 0.75])
    df_rfv["R_quartil"] = df_rfv["Recencia"].apply(recencia_class, args=("Recencia", quartis))
    df_rfv["F_quartil"] = df_rfv["Frequencia"].apply(freq_val_class, args=("Frequencia", quartis))
    df_rfv["V_quartil"] = df_rfv["Valor"].apply(freq_val_class, args=("Valor", quartis))
    df_rfv["RFV_Score"] = df_rfv["R_quartil"] + df_rfv["F_quartil"] + df_rfv["V_quartil"]

    dict_acoes = {
        "AAA": "Enviar cupons, solicitar indicacoes e priorizar novidades ou amostras.",
        "DDD": "Clientes com baixa compra e baixo valor. Manter em acompanhamento sem acao imediata.",
        "DAA": "Clientes valiosos que ficaram distantes. Criar campanha de recuperacao.",
        "CAA": "Clientes importantes com queda recente. Oferecer incentivo para nova compra.",
    }
    df_rfv["acao_marketing_crm"] = df_rfv["RFV_Score"].map(dict_acoes).fillna("Monitorar comportamento do grupo.")

    return df_rfv, dia_atual


def main():
    st.set_page_config(
        page_title="RFV | Weslei Granza",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_style()

    st.markdown(
        """
        <div class="hero">
            <h1>Segmentacao RFV</h1>
            <p><strong>Por:</strong> Weslei Granza | <strong>Data:</strong> 28 de maio de 2026</p>
            <p>Ferramenta em Streamlit para classificar clientes por recencia, frequencia e valor.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("Entrada de dados")
    st.sidebar.caption("Envie uma base CSV/XLSX ou use o arquivo demonstrativo do projeto.")
    uploaded_file = st.sidebar.file_uploader("Arquivo de compras", type=["csv", "xlsx"])
    use_demo = st.sidebar.toggle("Usar base demonstrativa", value=uploaded_file is None)

    try:
        if uploaded_file is not None:
            df_compras = load_uploaded_data(uploaded_file)
            source_label = uploaded_file.name
        elif use_demo:
            df_compras = load_demo_data()
            source_label = str(DEMO_FILE.name)
        else:
            st.info("Envie um arquivo ou ative a base demonstrativa para iniciar a analise.")
            return

        df_rfv, dia_atual = build_rfv(df_compras)
    except Exception as exc:
        st.error(f"Nao foi possivel processar a base: {exc}")
        return

    st.caption(f"Base em uso: {source_label}")

    metric_cols = st.columns(4)
    metric_cols[0].metric("Clientes", f"{df_rfv.shape[0]:,}".replace(",", "."))
    metric_cols[1].metric("Data mais recente", dia_atual.strftime("%d/%m/%Y"))
    metric_cols[2].metric("Valor total", f"R$ {df_rfv['Valor'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    metric_cols[3].metric("Score mais comum", df_rfv["RFV_Score"].mode().iat[0])

    st.divider()
    st.subheader("Resumo da base")
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.dataframe(df_rfv.head(20), use_container_width=True)
    with col2:
        st.write("Distribuicao dos grupos RFV")
        st.bar_chart(df_rfv["RFV_Score"].value_counts().sort_index())

    st.subheader("Clientes de maior prioridade")
    st.write(
        "A classificacao usa quartis: menor recencia indica cliente mais recente, "
        "enquanto maior frequencia e maior valor indicam melhor desempenho."
    )
    st.dataframe(
        df_rfv[df_rfv["RFV_Score"] == "AAA"].sort_values("Valor", ascending=False).head(10),
        use_container_width=True,
    )

    st.subheader("Acoes de marketing/CRM")
    st.dataframe(
        df_rfv["acao_marketing_crm"].value_counts().rename_axis("acao").reset_index(name="clientes"),
        use_container_width=True,
    )

    st.download_button(
        label="Baixar tabela RFV em Excel",
        data=to_excel(df_rfv),
        file_name="RFV_Weslei_Granza.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
