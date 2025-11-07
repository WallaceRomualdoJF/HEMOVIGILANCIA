import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
def carregar_dados(file_path):
    
    try:
        df = pd.read_csv(file_path, sep=';', encoding='ISO-8859-1')
        print("Dados carregados com sucesso!")
        print(f"Número de linhas: {df.shape[0]}")
        print(f"Número de colunas: {df.shape[1]}")
        return df
    except FileNotFoundError:
        print(f"Erro: O arquivo {file_path} não foi encontrado.")
        return None
    except Exception as e:
        print(f"Ocorreu um erro ao carregar o arquivo: {e}")
        return None
def analise_exploratoria(df):
    print("\n--- Análise Exploratória dos Dados ---")
    print("\nPrimeiras 5 linhas do DataFrame:")
    print(df.head())
    print("\nInformações gerais do DataFrame:")
    df.info()
    print("\nEstatísticas descritivas:")
    print(df.describe(include='all'))

    print("\nValores ausentes por coluna:")
    missing_data = df.isnull().sum()
    print(missing_data[missing_data > 0])

    plt.figure(figsize=(12, 6))
    sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
    plt.title('Mapa de Calor de Valores Ausentes')
    plt.savefig('reports/heatmap_missing_data.png')
    plt.close()

    print("\nNúmero de linhas duplicadas:", df.duplicated().sum())

    print("\nDistribuição de STATUS_ANALISE:")
    print(df["STATUS_ANALISE"].value_counts())
    sns.countplot(y='STATUS_ANALISE', data=df, palette='viridis')
    plt.title('Distribuição de Status de Análise')
    plt.savefig('reports/distribuicao_status_analise.png')
    plt.close()

    print("\nDistribuição de GRAU_RISCO:")
    print(df["GRAU_RISCO"].value_counts())
    sns.countplot(y='GRAU_RISCO', data=df, palette='magma')
    plt.title('Distribuição de Grau de Risco')
    plt.savefig('reports/distribuicao_grau_risco.png')
    plt.close()

    print("\nDistribuição de TIPO_REACAO_TRANSFUSIONAL (Top 10):")
    print(df['TIPO_REACAO_TRANSFUSIONAL'].value_counts().head(10))
    plt.figure(figsize=(10, 7))
    sns.countplot(y='TIPO_REACAO_TRANSFUSIONAL', data=df, order=df['TIPO_REACAO_TRANSFUSIONAL'].value_counts().head(10).index, palette='cividis')
    plt.title('Top 10 Tipos de Reação Transfusional')
    plt.savefig('reports/top10_reacao_transfusional.png')
    plt.close()

    print("\nDistribuição de UF_NOTIFICACAO (Top 10):")
    print(df['UF_NOTIFICACAO'].value_counts().head(10))
    plt.figure(figsize=(10, 7))
    sns.countplot(y='UF_NOTIFICACAO', data=df, order=df['UF_NOTIFICACAO'].value_counts().head(10).index, palette='plasma')
    plt.title('Top 10 Estados com Mais Notificações')
    plt.savefig('reports/top10_uf_notificacao.png')
    plt.close()

    df["DATA_OCORRENCIA_EVENTO"] = pd.to_datetime(df["DATA_OCORRENCIA_EVENTO"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
    df["DATA_NOTIFICACAO_EVENTO"] = pd.to_datetime(df["DATA_NOTIFICACAO_EVENTO"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
    df['ANO_OCORRENCIA'] = df['DATA_OCORRENCIA_EVENTO'].dt.year

    plt.figure(figsize=(12, 6))
    sns.countplot(x='ANO_OCORRENCIA', data=df.dropna(subset=['ANO_OCORRENCIA']), palette='viridis')
    plt.title('Número de Notificações por Ano de Ocorrência')
    plt.xticks(rotation=45)
    plt.savefig('reports/notificacoes_por_ano.png')
    plt.close()

def identificar_vulnerabilidades(df):
    """Identifica vulnerabilidades e problemas de proteção de dados."""
    print("\n--- Identificação de Vulnerabilidades e Problemas de Proteção de Dados ---")

    print("\nVerificação de valores inesperados em colunas chave:")
    valores_esperados_grau_risco = ['Grau I   - Leve', 'Grau II  - Moderado', 'Grau III - Grave', 'Grau IV  - Óbito']
    valores_atuais_grau_risco = df['GRAU_RISCO'].unique()
    for valor in valores_atuais_grau_risco:
        if valor not in valores_esperados_grau_risco and pd.notna(valor):
            print(f"  -> Alerta: Valor inesperado em GRAU_RISCO: {valor}")

    inconsistencias_datas = df[df['DATA_NOTIFICACAO_EVENTO'] < df['DATA_OCORRENCIA_EVENTO']]
    print(f"\nNúmero de registros com data de notificação anterior à de ocorrência: {len(inconsistencias_datas)}")

    df['TEMPO_NOTIFICACAO_DIAS'] = (df['DATA_NOTIFICACAO_EVENTO'] - df['DATA_OCORRENCIA_EVENTO']).dt.days
    atrasos_excessivos = df[df['TEMPO_NOTIFICACAO_DIAS'] > 365]
    print(f"\nNúmero de registros com atraso de notificação superior a 365 dias: {len(atrasos_excessivos)}")

    plt.figure(figsize=(10, 6))
    sns.histplot(df['TEMPO_NOTIFICACAO_DIAS'].dropna(), bins=50, kde=True)
    plt.title('Distribuição do Tempo entre Ocorrência e Notificação (em dias)')
    plt.xlabel('Tempo (dias)')
    plt.ylabel('Frequência')
    plt.xlim(0, df["TEMPO_NOTIFICACAO_DIAS"].quantile(0.99))
    plt.savefig("reports/distribuicao_tempo_notificacao.png")
    plt.close()

    combinacao_faixa_cidade = df.groupby(['FAIXA_ETARIA_PACIENTE', 'CIDADE_NOTIFICACAO']).size().reset_index(name='Contagem')
    combinacao_faixa_cidade_baixa_contagem = combinacao_faixa_cidade[combinacao_faixa_cidade['Contagem'] <= 5]
    print("\nCombinações de Faixa Etária e Cidade com baixa contagem:")
    print(combinacao_faixa_cidade_baixa_contagem.sort_values(by='Contagem').head())

def engenharia_features(df):
    """Realiza a engenharia de features para os modelos de IA."""
    print("\n--- Engenharia de Features para Modelos de IA ---")
    df['TEMPO_NOTIFICACAO_DIAS'] = (df['DATA_NOTIFICACAO_EVENTO'] - df['DATA_OCORRENCIA_EVENTO']).dt.days
    df['ANO_OCORRENCIA'] = df['DATA_OCORRENCIA_EVENTO'].dt.year
    df['MES_OCORRENCIA'] = df['DATA_OCORRENCIA_EVENTO'].dt.month
    df['DIA_SEMANA_OCORRENCIA'] = df['DATA_OCORRENCIA_EVENTO'].dt.dayofweek
    df['HORA_OCORRENCIA'] = df['DATA_OCORRENCIA_EVENTO'].dt.hour

    mapeamento_risco = {
        'Grau I   - Leve': 1,
        'Grau II  - Moderado': 2,
        'Grau III - Grave': 3,
        'Grau IV  - Óbito': 4
    }
    df["GRAU_RISCO_NUM"] = df["GRAU_RISCO"].map(mapeamento_risco)

    categorical_cols = [
        'PRODUTO_MOTIVO',
        'TIPO_REACAO_TRANSFUSIONAL',
        'CATEGORIA_NOTIFICADOR',
        'TIPO_HEMOCOMPONENTE',
        'FAIXA_ETARIA_PACIENTE',
        'UF_NOTIFICACAO',
        'DS_TEMPORALIDADE_REACAO',
        'TIPO_EVENTO_ADVERSO',
        'ETAPA_CICLO_SANGUE'
    ]

    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna('NA_CATEGORY')

    df_encoded = pd.get_dummies(df, columns=categorical_cols, prefix=categorical_cols)

    df_model = df_encoded.drop(columns=[
        'NU_NOTIFICACAO', 'DATA_OCORRENCIA_EVENTO', 'DATA_NOTIFICACAO_EVENTO',
        'GRAU_RISCO', 'CIDADE_NOTIFICACAO', 'DS_ESPECIFICACAO_EVENTO'
    ], errors='ignore')

    for col in df_model.select_dtypes(include=np.number).columns:
        df_model[col] = df_model[col].fillna(df_model[col].median())
    for col in df_model.columns:
        if df_model[col].dtype == 'object':
            df_model = df_model.drop(columns=[col])

    return df_model

def aplicar_ia(df_model):
    """Aplica modelos de IA para análise e solução de problemas."""
    print("\n--- Aplicação de IA para Análise e Solução de Problemas ---")

    X = df_model.drop(columns=["GRAU_RISCO_NUM"], errors='ignore')
    y = df_model["GRAU_RISCO_NUM"]
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.dropna(axis=1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("\nRelatório de Classificação do Modelo Random Forest:")
    print(classification_report(y_test, y_pred))
    print("\nMatriz de Confusão:")
    print(confusion_matrix(y_test, y_pred))
    print(f"\nAcurácia do Modelo: {accuracy_score(y_test, y_pred):.4f}")

    feature_importances = pd.Series(model.feature_importances_, index=X.columns)
    print("\nTop 10 Features Mais Importantes para Prever o Grau de Risco:")
    print(feature_importances.nlargest(10))

    plt.figure(figsize=(12, 7))
    sns.barplot(x=feature_importances.nlargest(10).values, y=feature_importances.nlargest(10).index, palette='viridis')
    plt.title('Importância das Features na Previsão do Grau de Risco')
    plt.xlabel('Importância')
    plt.ylabel('Feature')
    plt.savefig('reports/feature_importance.png')
    plt.close()
    iso_forest = IsolationForest(random_state=42, contamination=0.01)
    iso_forest.fit(X)
    df_model["ANOMALIA_ISO_FOREST"] = iso_forest.predict(X)

    print("\nNúmero de Anomalias Detectadas pelo Isolation Forest:")
    print(df_model["ANOMALIA_ISO_FOREST"].value_counts())

    print("\nPrimeiras 10 Notificações Classificadas como Anomalias:")
    print(df_model[df_model["ANOMALIA_ISO_FOREST"] == -1].head(10))


if __name__ == "__main__":
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    sns.set_style('whitegrid')

    file_path = 'data/DADOS_ABERTOS_HEMOVIGILANCIA_UTF8.csv'

    df = carregar_dados(file_path)

    if df is not None:
        analise_exploratoria(df)
        identificar_vulnerabilidades(df)
        df_model = engenharia_features(df.copy())
        aplicar_ia(df_model)


