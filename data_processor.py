import pandas as pd
import numpy as np
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

CAMINHO_DADOS = 'data/DADOS_ABERTOS_HEMOVIGILANCIA_UTF8.csv'
CAMINHO_DADOS_PROCESSADO = 'data/DADOS_HEMOVIGILANCIA_PROCESSADO.csv'

def pre_processar_dados(df):
    """Realiza o pré-processamento básico e cria colunas de data."""
    
    df.columns = df.columns.str.upper().str.strip()
    
    if "DATA_OCORRENCIA_EVENTO" in df.columns:
        df["DATA_OCORRENCIA_EVENTO"] = pd.to_datetime(df["DATA_OCORRENCIA_EVENTO"], errors="coerce", dayfirst=True)
        df["ANO"] = df["DATA_OCORRENCIA_EVENTO"].dt.year
        df["MES"] = df["DATA_OCORRENCIA_EVENTO"].dt.month
        df = df.dropna(subset=['DATA_OCORRENCIA_EVENTO'])
    
    df = df.drop(columns=['ID_NOTIFICACAO', 'DATA_NOTIFICACAO_EVENTO'], errors='ignore')
    
    return df

def detectar_anomalias(df):
    
    df_modelo = df.copy()
    
    features = ['TIPO_REACAO_TRANSFUSIONAL', 'GRAU_RISCO', 'IDADE_PACIENTE']
    
    if 'IDADE_PACIENTE' not in df_modelo.columns:
        df_modelo['IDADE_PACIENTE'] = 0
    
    df_modelo['IDADE_PACIENTE'] = pd.to_numeric(df_modelo['IDADE_PACIENTE'], errors='coerce').fillna(df_modelo['IDADE_PACIENTE'].median())
    df_modelo['GRAU_RISCO'] = df_modelo['GRAU_RISCO'].fillna('NAO INFORMADO')
    df_modelo['TIPO_REACAO_TRANSFUSIONAL'] = df_modelo['TIPO_REACAO_TRANSFUSIONAL'].fillna('NAO INFORMADO')
    
    le = LabelEncoder()
    df_modelo['TIPO_REACAO_COD'] = le.fit_transform(df_modelo['TIPO_REACAO_TRANSFUSIONAL'])
    df_modelo['GRAU_RISCO_COD'] = le.fit_transform(df_modelo['GRAU_RISCO'])
    
    cols_modelo = ['IDADE_PACIENTE', 'TIPO_REACAO_COD', 'GRAU_RISCO_COD']
    X = df_modelo[[col for col in cols_modelo if col in df_modelo.columns]]
    
    model = IsolationForest(random_state=42, contamination='auto')
    model.fit(X)
    
    df['ANOMALY_LABEL'] = model.predict(X)
    
    df['anomalias'] = df['ANOMALY_LABEL'].apply(lambda x: 1 if x == -1 else 0)
    df = df.drop(columns=['ANOMALY_LABEL'], errors='ignore')
    
    return df

def processar_dados_principal():
    """Função principal para processar e salvar os dados."""
    if not os.path.exists(CAMINHO_DADOS):
        print(f"❌ Erro: Arquivo de dados não encontrado em {CAMINHO_DADOS}. Execute o crawler primeiro.")
        return False
        
    try:

        df = pd.read_csv(CAMINHO_DADOS, sep=';', encoding='ISO-8859-1', on_bad_lines='skip')
        
        df = pre_processar_dados(df)
        
        df = detectar_anomalias(df)
        
        df.to_csv(CAMINHO_DADOS_PROCESSADO, sep=';', encoding='ISO-8859-1', index=False)
        print(f"✅ Dados processados e anomalias detectadas. Salvo em {CAMINHO_DADOS_PROCESSADO}")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o processamento dos dados: {e}")
        return False

if __name__ == "__main__":
    processar_dados_principal()

