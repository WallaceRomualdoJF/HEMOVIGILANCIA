try:
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    import plotly.figure_factory as ff
    import geopandas as gpd
except Exception as e:
    raise ImportError(
        "Missing required packages for this dashboard. Install them with:\n"
        "    pip install streamlit pandas plotly geopandas scikit-learn numpy\n"
        "or using conda:\n"
        "    conda install -c conda-forge streamlit pandas plotly geopandas scikit-learn numpy\n"
        f"\nOriginal error: {e}"
    )
import os
import json
from sklearn.linear_model import LinearRegression
import numpy as np

st.set_page_config(page_title="Dashboard Hemovigilância", layout="wide")
st.title("📊 Dashboard Interativo de Hemovigilância")
st.markdown("### Análise de notificações, anomalias e padrões regionais com risco e previsão")

@st.cache_data
def carregar_dados():
    if os.path.exists("reports/resultado_com_anomalias.xlsx"):
        df = pd.read_excel("reports/resultado_com_anomalias.xlsx")
    elif os.path.exists("data/DADOS_ABERTOS_HEMOVIGILANCIA_UTF8.csv"):
        df = pd.read_csv("data/DADOS_ABERTOS_HEMOVIGILANCIA_UTF8.csv", sep=";", encoding="ISO-8859-1")
    else:
        st.error("❌ Nenhum arquivo de dados encontrado.")
        return pd.DataFrame()
    
    df.columns = df.columns.str.upper().str.strip()
    
    if "DATA_OCORRENCIA_EVENTO" in df.columns:
        df["DATA_OCORRENCIA_EVENTO"] = pd.to_datetime(df["DATA_OCORRENCIA_EVENTO"], errors="coerce", dayfirst=True)
        df["ANO"] = df["DATA_OCORRENCIA_EVENTO"].dt.year
    elif "DATA_NOTIFICACAO_EVENTO" in df.columns:
        df["DATA_NOTIFICACAO_EVENTO"] = pd.to_datetime(df["DATA_NOTIFICACAO_EVENTO"], errors="coerce", dayfirst=True)
        df["ANO"] = df["DATA_NOTIFICACAO_EVENTO"].dt.year

    if "ANOMALY_LABEL" in df.columns:
        df = df.rename(columns={"ANOMALY_LABEL": "anomalias"})
    
    if "anomalias" in df.columns:
        df["anomalias"] = pd.to_numeric(df["anomalias"], errors="coerce").fillna(0).astype(int)
    return df

df = carregar_dados()

if not df.empty:

    st.sidebar.header("🔍 Filtros de Análise")
    uf_options = sorted(df["UF_NOTIFICACAO"].dropna().unique()) if "UF_NOTIFICACAO" in df.columns else []
    tipo_evento_options = sorted(df["TIPO_REACAO_TRANSFUSIONAL"].dropna().unique()) if "TIPO_REACAO_TRANSFUSIONAL" in df.columns else []
    ano_options = sorted(df["ANO"].dropna().unique()) if "ANO" in df.columns else []

    uf_sel = st.sidebar.multiselect("Selecione UF(s):", uf_options, default=uf_options)
    tipo_sel = st.sidebar.multiselect("Selecione Tipo de Evento:", tipo_evento_options, default=tipo_evento_options)
    ano_sel = st.sidebar.multiselect("Selecione Ano(s):", ano_options, default=ano_options)

    df_filtrado = df[
        (df["UF_NOTIFICACAO"].isin(uf_sel) if "UF_NOTIFICACAO" in df.columns else True) &
        (df["TIPO_REACAO_TRANSFUSIONAL"].isin(tipo_sel) if "TIPO_REACAO_TRANSFUSIONAL" in df.columns else True) &
        (df["ANO"].isin(ano_sel) if "ANO" in df.columns else True)
    ]

    aba1, aba2, aba3, aba4 = st.tabs(["📈 Visão Geral", "📊 Distribuições", "🗺️ Mapa Brasil", "🧩 Correlação & Dados"])

    with aba1:
        st.subheader("📈 Métricas Gerais")
        col1, col2, col3 = st.columns(3)

        total_notificacoes = len(df_filtrado)
        total_anomalias = df_filtrado["anomalias"].sum() if "anomalias" in df_filtrado.columns else 0
        perc_anomalias = (total_anomalias / total_notificacoes * 100) if total_notificacoes > 0 else 0

        col1.metric("Total de Notificações", f"{total_notificacoes:,}".replace(",", "."))
        col2.metric("Casos Anômalos", f"{total_anomalias:,}".replace(",", "."))
        col3.metric("Percentual de Anomalias", f"{perc_anomalias:.2f}%")

        st.markdown("---")
        st.subheader("📅 Tendência Temporal das Notificações com Previsão")

        if "ANO" in df_filtrado.columns:
            df_ano = df_filtrado.groupby("ANO").size().reset_index(name="Notificações")
            X = df_ano["ANO"].values.reshape(-1,1)
            y = df_ano["Notificações"].values
            model = LinearRegression().fit(X, y)
            proximo_ano = df_ano["ANO"].max() + 1
            previsao = int(model.predict(np.array([[proximo_ano]]))[0])
            
            df_prev = pd.concat([df_ano, pd.DataFrame([{"ANO": proximo_ano, "Notificações": previsao}])], ignore_index=True)
            fig_ano = px.line(df_prev, x="ANO", y="Notificações", markers=True, title="Tendência de Notificações + Previsão")
            fig_ano.add_scatter(x=[proximo_ano], y=[previsao], mode='markers+text', text=[f"Prev: {previsao}"], textposition="top center", marker=dict(color="red", size=12))
            st.plotly_chart(fig_ano, use_container_width=True)

            st.info(f"📌 Previsão de notificações para {proximo_ano}: {previsao}")

    with aba2:
        st.subheader("📍 Distribuição Regional e por Tipo de Evento")
        col1, col2 = st.columns(2)

        with col1:
            if "UF_NOTIFICACAO" in df_filtrado.columns:
                df_uf = df_filtrado["UF_NOTIFICACAO"].value_counts().reset_index()
                df_uf.columns = ["UF", "Quantidade"]
                fig_uf = px.bar(df_uf, x="UF", y="Quantidade", title="Notificações por UF", color="UF")
                st.plotly_chart(fig_uf, use_container_width=True)

        with col2:
            if "TIPO_REACAO_TRANSFUSIONAL" in df_filtrado.columns:
                df_tipo = df_filtrado["TIPO_REACAO_TRANSFUSIONAL"].value_counts().reset_index()
                df_tipo.columns = ["Tipo de Evento", "Quantidade"]
                fig_tipo = px.bar(df_tipo, x="Tipo de Evento", y="Quantidade", title="Tipos de Eventos Notificados", color="Tipo de Evento")
                st.plotly_chart(fig_tipo, use_container_width=True)

        st.markdown("---")
        st.subheader("⚠️ UFs com maior risco de anomalias")
        if "anomalias" in df_filtrado.columns and "UF_NOTIFICACAO" in df_filtrado.columns:
            risco_uf = df_filtrado.groupby("UF_NOTIFICACAO")["anomalias"].sum().reset_index()
            risco_uf = risco_uf.sort_values("anomalias", ascending=False)
            st.dataframe(risco_uf.head(5), use_container_width=True)
            st.info(f"⚠️ UF com maior risco: {risco_uf.iloc[0]['UF_NOTIFICACAO']} ({risco_uf.iloc[0]['anomalias']} anomalias)")

with aba3:
    st.subheader("🗺️ Mapa Interativo de Notificações por UF (Risco)")

    if "anomalias" in df_filtrado.columns and "UF_NOTIFICACAO" in df_filtrado.columns:
        
        df_map = df_filtrado.groupby("UF_NOTIFICACAO")["anomalias"].sum().reset_index()
        df_map.columns = ["UF", "Risco"]

        with open("data/br_states.json", "r", encoding="utf-8") as f:
            brazil_geojson = json.load(f)

        df_map["id_uf"] = df_map["UF"].astype(str)

        coordenadas_estados = {
            "AC": [-9.02, -70.81], "AL": [-9.57, -36.78], "AP": [1.41, -51.77], "AM": [-3.47, -65.10],
            "BA": [-12.97, -41.65], "CE": [-5.20, -39.53], "DF": [-15.78, -47.93], "ES": [-19.19, -40.34],
            "GO": [-15.98, -49.86], "MA": [-5.42, -45.44], "MT": [-12.64, -55.42], "MS": [-20.51, -54.54],
            "MG": [-18.10, -44.38], "PA": [-3.79, -52.48], "PB": [-7.24, -36.78], "PR": [-24.89, -51.55],
            "PE": [-8.38, -37.86], "PI": [-7.72, -42.73], "RJ": [-22.25, -42.66], "RN": [-5.79, -36.59],
            "RS": [-30.17, -53.50], "RO": [-10.83, -63.34], "RR": [1.99, -61.33], "SC": [-27.33, -50.41],
            "SP": [-22.19, -48.79], "SE": [-10.57, -37.45], "TO": [-10.25, -48.30]
        }

        df_map["lat"] = df_map["UF"].map(lambda x: coordenadas_estados.get(x, [None, None])[0])
        df_map["lon"] = df_map["UF"].map(lambda x: coordenadas_estados.get(x, [None, None])[1])

        fig_map = px.choropleth(
            df_map,
            geojson=brazil_geojson,
            locations="UF",
            featureidkey="properties.sigla",
            color="Risco",
            hover_name="UF",
            color_continuous_scale="Reds",
            title="🗺️ Risco de Anomalias por Estado (Brasil)",
            scope="south america"
        )

        fig_pontos = px.scatter_geo(
            df_map,
            lat="lat",
            lon="lon",
            size="Risco",
            color="Risco",
            color_continuous_scale="Reds",
            hover_name="UF",
            text="UF",
            size_max=25
        )

        for trace in fig_pontos.data:
            fig_map.add_trace(trace)

        fig_map.update_geos(
            projection_type="mercator",
            fitbounds="locations",
            showcoastlines=True,
            coastlinecolor="gray",
            showland=True,
            landcolor="lightgray"
        )

        fig_map.update_layout(
            margin={"r":0,"t":50,"l":0,"b":0},
            coloraxis_colorbar=dict(title="Nº de Anomalias"),
        )

        st.plotly_chart(fig_map, use_container_width=True)

    with aba4:
        st.subheader("📊 Análise de Correlação Automática")
        numeric_cols = df_filtrado.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) >= 2:
            corr_matrix = df_filtrado[numeric_cols].corr()
            fig_corr = ff.create_annotated_heatmap(z=corr_matrix.values, x=list(corr_matrix.columns),
                                                   y=list(corr_matrix.columns), annotation_text=corr_matrix.round(2).values,
                                                   colorscale='Viridis')
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Não há colunas numéricas suficientes para calcular correlação.")

        st.markdown("---")
        st.subheader("🧾 Dados Filtrados")
        st.dataframe(df_filtrado.head(1000), use_container_width=True)
        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar CSV Filtrado", data=csv, file_name="hemovigilancia_filtrado.csv", mime="text/csv")