import os
import sys
import logging

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

import importlib

try:
    ydata_profiling = importlib.import_module("ydata_profiling")
    ProfileReport = getattr(ydata_profiling, "ProfileReport", None)
    HAS_PROFILE = ProfileReport is not None
except Exception:
    ProfileReport = None
    HAS_PROFILE = False

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
REPORTS_DIR = os.path.join(ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("hemovigilancia")

def carregar_dados(nome_arquivo="DADOS_ABERTOS_HEMOVIGILANCIA_UTF8.csv", encoding="ISO-8859-1"):
    caminho = os.path.join(DATA_DIR, nome_arquivo)
    logger.info(f"Carregando dados de: {caminho}")
    if not os.path.exists(caminho):
        logger.error("Arquivo de dados não encontrado. Verifique o caminho.")
        raise FileNotFoundError(caminho)
    df = pd.read_csv(caminho, encoding=encoding, low_memory=False, sep=";")
    logger.info(f"Dados carregados: {df.shape[0]} linhas, {df.shape[1]} colunas")
    return df

def detectar_campos_sensiveis(df):
    possíveis = []
    for col in df.columns:
        nome = col.lower()
        if any(k in nome for k in ["cpf", "nome", "endereco", "email", "telefone", "celular", "rg"]):
            possíveis.append(col)
    
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().astype(str).head(200)
        if sample.str.match(r"^\d{3}\.?\d{3}\.?\d{3}\-?\d{2}$").any():
            if col not in possíveis:
                possíveis.append(col)
    return possíveis

def anonimizar(df, cols):
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(lambda x: "<ANONIMIZADO>" if pd.notna(x) and x.strip()!="" else x)
    return df

def resumo_geral(df):
    info = {
        "linhas": df.shape[0],
        "colunas": df.shape[1],
        "nulos_por_coluna": df.isna().sum().to_dict(),
        "tipos": df.dtypes.apply(lambda x: x.name).to_dict(),
        "colunas_sensiveis": detectar_campos_sensiveis(df)
    }
    return info

def salvar_figura(fig, nome):
    caminho = os.path.join(REPORTS_DIR, nome)
    fig.savefig(caminho, bbox_inches="tight", dpi=150)
    plt.close(fig)
    logger.info(f"Gráfico salvo: {caminho}")

def plot_heatmap_missing(df):
    fig, ax = plt.subplots(figsize=(12,6))
    sns.heatmap(df.isna(), cbar=False, yticklabels=False, ax=ax)
    ax.set_title("Heatmap - Dados ausentes (True = ausente)")
    salvar_figura(fig, "heatmap_missing_data_avancado.png")

def plot_distribuicao_categorica(df, coluna, topn=10):
    if coluna not in df.columns:
        return
    serie = df[coluna].fillna("NA")
    top = serie.value_counts().head(topn)
    fig, ax = plt.subplots(figsize=(8,5))
    sns.barplot(x=top.values, y=top.index, ax=ax)
    ax.set_xlabel("Contagem")
    ax.set_title(f"Top {topn} - {coluna}")
    salvar_figura(fig, f"top_{coluna}.png")

def plot_timeseries_count(df, data_col, freq='Y'):
    if data_col not in df.columns:
        return
    try:
        s = pd.to_datetime(df[data_col], errors="coerce", dayfirst=True)
        counts = s.dt.to_period(freq).value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(10,4))
        counts.plot(ax=ax)
        ax.set_title(f"Contagem por período ({data_col})")
        salvar_figura(fig, f"timeseries_{data_col}.png")
    except Exception as e:
        logger.warning(f"Falha ao plotar série temporal: {e}")

def limpeza_basica(df):
    df = df.copy()
    
    df.columns = [c.strip() for c in df.columns]
    
    for c in df.columns:
        if "data" in c.lower() or "dt_" in c.lower() or "ano" in c.lower():
            try:
                df[c] = pd.to_datetime(df[c], errors="coerce")
            except Exception:
                pass
    
    return df

def preparar_numericos(df):
    num = df.select_dtypes(include=["int64","float64"]).copy()
    num = num.fillna(0)
    return num

def detectar_anomalias(df, n_estimators=100, contamination=0.03, random_state=42):
    num = preparar_numericos(df)
    if num.shape[1] == 0:
        logger.warning("Nenhuma coluna numérica disponível para detecção de anomalias.")
        return pd.Series(index=df.index, data=0, name="anomaly_label")
    scaler = StandardScaler()
    X = scaler.fit_transform(num)
    modelo = IsolationForest(n_estimators=n_estimators, contamination=contamination, random_state=random_state)
    modelo.fit(X)
    labels = modelo.predict(X)
    labels = pd.Series(labels, index=df.index).map({1: 0, -1: 1}).astype(int)
    df["anomaly_label"] = labels
    logger.info(f"Anomalias detectadas: {int(labels.sum())} registros ({labels.mean():.2%})")
    return df["anomaly_label"]

def gerar_relatorio_excel(df, nome_arquivo="relatorio_analise.xlsx"):
    caminho = os.path.join(REPORTS_DIR, nome_arquivo)
    try:
        df.to_excel(caminho, index=False)
        logger.info(f"Relatório Excel gerado: {caminho}")
    except Exception as e:
        logger.error(f"Erro ao gerar Excel: {e}")

def gerar_relatorio_profiler(df, nome_arquivo="relatorio_profile.html"):
    if not HAS_PROFILE:
        logger.warning("ydata_profiling (pandas-profiling) não disponível. Ignorando relatório automático.")
        return
    caminho = os.path.join(REPORTS_DIR, nome_arquivo)
    profile = ProfileReport(df, title="Relatório de Perfil - Hemovigilância", minimal=True)
    profile.to_file(caminho)
    logger.info(f"Relatório profile gerado: {caminho}")

def main():
    logger.info("Iniciando análise avançada de Hemovigilância")
    df = carregar_dados()
    info = resumo_geral(df)
    logger.info(f"Resumo: linhas={info['linhas']} colunas={info['colunas']}")
    logger.info(f"Campos sensíveis detectados: {info['colunas_sensiveis']}")

    df_clean = limpeza_basica(df)

    sensiveis = info["colunas_sensiveis"]
    if sensiveis:
        logger.info("Anonimizando campos sensíveis (substituição por <ANONIMIZADO>)")
        df_anon = anonimizar(df_clean, sensiveis)
    else:
        df_anon = df_clean

    plot_heatmap_missing(df_anon)
    
    if "UF_NOTIFICACAO" in df_anon.columns:
        plot_distribuicao_categorica(df_anon, "UF_NOTIFICACAO", topn=15)
    
    candidates = [c for c in df_anon.columns if "data" in c.lower() or "ano" in c.lower()]
    if candidates:
        plot_timeseries_count(df_anon, candidates[0], freq='Y')

    anom = detectar_anomalias(df_anon, contamination=0.03)
    df_anon["anomaly_label"] = anom

    gerar_relatorio_excel(df_anon, nome_arquivo="resultado_com_anomalias.xlsx")

    gerar_relatorio_profiler(df_anon, nome_arquivo="relatorio_profile.html")

    logger.info("Análise finalizada. Verifique a pasta /reports para gráficos e relatórios.")

if __name__ == "__main__":
    main()
