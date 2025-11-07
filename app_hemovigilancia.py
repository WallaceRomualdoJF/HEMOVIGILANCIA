from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from functools import wraps
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
from crawler_hemovigilancia import HemovigilanciaCrawler

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = 'hemovigilancia_secret_key_2025'

CAMINHO_DADOS_ORIGINAL = 'data/DADOS_ABERTOS_HEMOVIGILANCIA_UTF8.csv'
CAMINHO_DADOS = 'data/DADOS_HEMOVIGILANCIA_PROCESSADO.csv' # Novo arquivo com anomalias
CAMINHO_DADOS_BACKUP = 'data/old.DADOS_ABERTOS_HEMOVIGILANCIA_UTF8.csv'
CAMINHO_GEOJSON = 'data/br_states.json'

dados_cache = {
    'df': None,
    'timestamp': None,
    'ultima_atualizacao': None
}


def carregar_dados():
    """Carrega os dados de hemovigilância com cache."""
    global dados_cache
    
    if dados_cache['df'] is not None and dados_cache['timestamp'] is not None:
        return dados_cache['df'].copy()
    
    try:
        if os.path.exists(CAMINHO_DADOS):
            df = pd.read_csv(CAMINHO_DADOS, sep=';', encoding='ISO-8859-1', on_bad_lines='skip')
        elif os.path.exists(CAMINHO_DADOS_BACKUP):
            df = pd.read_csv(CAMINHO_DADOS_BACKUP, sep=';', encoding='ISO-8859-1', on_bad_lines='skip')
        else:
            if os.path.exists(CAMINHO_DADOS_ORIGINAL):
                df = pd.read_csv(CAMINHO_DADOS_ORIGINAL, sep=';', encoding='ISO-8859-1', on_bad_lines='skip')
            else:
                return pd.DataFrame()
        
        df.columns = df.columns.str.upper().str.strip()
        
        if "DATA_OCORRENCIA_EVENTO" in df.columns:
            df["DATA_OCORRENCIA_EVENTO"] = pd.to_datetime(df["DATA_OCORRENCIA_EVENTO"], errors="coerce", dayfirst=True)
            df["ANO"] = df["DATA_OCORRENCIA_EVENTO"].dt.year
            df["MES"] = df["DATA_OCORRENCIA_EVENTO"].dt.month
        elif "DATA_NOTIFICACAO_EVENTO" in df.columns:
            df["DATA_NOTIFICACAO_EVENTO"] = pd.to_datetime(df["DATA_NOTIFICACAO_EVENTO"], errors="coerce", dayfirst=True)
            df["ANO"] = df["DATA_NOTIFICACAO_EVENTO"].dt.year
            df["MES"] = df["DATA_NOTIFICACAO_EVENTO"].dt.month
        
        if "ANOMALIAS" in df.columns:
            df["anomalias"] = pd.to_numeric(df["ANOMALIAS"], errors="coerce").fillna(0).astype(int)
        else:
            df["anomalias"] = 0
        
        dados_cache['df'] = df.copy()
        dados_cache['timestamp'] = datetime.now()
        
        try:
            dados_cache['ultima_atualizacao'] = datetime.fromtimestamp(os.path.getmtime(CAMINHO_DADOS)).strftime('%d/%m/%Y %H:%M:%S')
        except FileNotFoundError:
            dados_cache['ultima_atualizacao'] = "N/A (Arquivo principal não encontrado)"
        
        return df
    
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def aplicar_filtros(df, filtros):
    """Aplica filtros ao DataFrame."""
    df_filtrado = df.copy()
    
    if 'ufs' in filtros and filtros['ufs']:
        df_filtrado = df_filtrado[df_filtrado['UF_NOTIFICACAO'].isin(filtros['ufs'])]
    
    if 'tipos_evento' in filtros and filtros['tipos_evento']:
        df_filtrado = df_filtrado[df_filtrado['TIPO_REACAO_TRANSFUSIONAL'].isin(filtros['tipos_evento'])]
    
    if 'anos' in filtros and filtros['anos']:
        df_filtrado = df_filtrado[df_filtrado['ANO'].isin(filtros['anos'])]
    
    if 'data_inicio' in filtros and filtros['data_inicio']:
        df_filtrado = df_filtrado[df_filtrado['DATA_OCORRENCIA_EVENTO'] >= pd.to_datetime(filtros['data_inicio'])]
    
    if 'data_fim' in filtros and filtros['data_fim']:
        df_filtrado = df_filtrado[df_filtrado['DATA_OCORRENCIA_EVENTO'] <= pd.to_datetime(filtros['data_fim'])]
    
    return df_filtrado

def obter_opcoes_filtro(df):
    """Obtém as opções disponíveis para filtros."""
    return {
        'ufs': sorted(df['UF_NOTIFICACAO'].dropna().unique().tolist()) if 'UF_NOTIFICACAO' in df.columns else [],
        'tipos_evento': sorted(df['TIPO_REACAO_TRANSFUSIONAL'].dropna().unique().tolist()) if 'TIPO_REACAO_TRANSFUSIONAL' in df.columns else [],
        'anos': sorted(df['ANO'].dropna().unique().astype(int).tolist()) if 'ANO' in df.columns else []
    }

def gerar_grafico_metricas(df_filtrado):
    """Gera gráfico de métricas principais."""
    total_notificacoes = len(df_filtrado)
    total_anomalias = df_filtrado['anomalias'].sum() if 'anomalias' in df_filtrado.columns else 0
    perc_anomalias = (total_anomalias / total_notificacoes * 100) if total_notificacoes > 0 else 0
    
    return {
        'total_notificacoes': total_notificacoes,
        'total_anomalias': total_anomalias,
        'perc_anomalias': round(perc_anomalias, 2)
    }

def gerar_grafico_timeline(df_filtrado):
    """Gera gráfico de tendência temporal."""
    if 'ANO' not in df_filtrado.columns or df_filtrado.empty:
        return None
    
    df_ano = df_filtrado.groupby('ANO').size().reset_index(name='Notificações')
    
    fig = px.line(df_ano, x='ANO', y='Notificações', markers=True,
                  title='Tendência de Notificações por Ano',
                  labels={'ANO': 'Ano', 'Notificações': 'Quantidade'})
    
    return fig.to_html(include_plotlyjs=False, div_id='timeline-chart')

def gerar_grafico_distribuicao_uf(df_filtrado):
    """Gera gráfico de distribuição por UF."""
    if 'UF_NOTIFICACAO' not in df_filtrado.columns or df_filtrado.empty:
        return None
    
    df_uf = df_filtrado['UF_NOTIFICACAO'].value_counts().reset_index()
    df_uf.columns = ['UF', 'Quantidade']
    
    fig = px.bar(df_uf, x='UF', y='Quantidade', title='Notificações por UF',
                 labels={'UF': 'Estado', 'Quantidade': 'Quantidade de Notificações'})
    
    return fig.to_html(include_plotlyjs=False, div_id='uf-chart')

def gerar_grafico_distribuicao_tipo(df_filtrado):
    """Gera gráfico de distribuição por tipo de evento."""
    if 'TIPO_REACAO_TRANSFUSIONAL' not in df_filtrado.columns or df_filtrado.empty:
        return None
    
    df_tipo = df_filtrado['TIPO_REACAO_TRANSFUSIONAL'].value_counts().reset_index()
    df_tipo.columns = ['Tipo de Evento', 'Quantidade']
    
    fig = px.bar(df_tipo, x='Tipo de Evento', y='Quantidade', 
                 title='Distribuição por Tipo de Evento',
                 labels={'Tipo de Evento': 'Tipo', 'Quantidade': 'Quantidade'})
    
    return fig.to_html(include_plotlyjs=False, div_id='tipo-chart')

def gerar_mapa_brasil(df_filtrado):

    if 'UF_NOTIFICACAO' not in df_filtrado.columns or df_filtrado.empty:
        return None
    
    try:
        with open(CAMINHO_GEOJSON, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        df_map_choropleth = df_filtrado.groupby('UF_NOTIFICACAO').size().reset_index(name='Notificações')
        df_map_choropleth.columns = ['UF', 'Notificações']
        
        fig = px.choropleth(df_map_choropleth, geojson=geojson_data, locations='UF',
                           featureidkey='properties.sigla', color='Notificações',
                           hover_name='UF', color_continuous_scale='Reds',
                           title='Mapa de Notificações por Estado')
        
        coordenadas_estados = {
            "AC": [-9.02, -70.81], "AL": [-9.57, -36.78], "AP": [1.41, -51.77], "AM": [-3.47, -65.10],
            "BA": [-12.97, -41.65], "CE": [-5.20, -39.53], "DF": [-15.78, -47.93], "ES": [-19.19, -40.34],
            "GO": [-15.98, -49.86], "MA": [-5.42, -45.44], "MT": [-12.64, -55.42], "MS": [-20.51, -54.54],
            "MG": [-18.10, -44.38], "PA": [-3.79, -52.48], "PB": [-7.24, -36.78], "PR": [-24.89, -51.55],
            "PE": [-8.38, -37.86], "PI": [-7.72, -42.73], "RJ": [-22.25, -42.66], "RN": [-5.79, -36.59],
            "RS": [-30.17, -53.50], "RO": [-10.83, -63.34], "RR": [1.99, -61.33], "SC": [-27.33, -50.41],
            "SP": [-22.19, -48.79], "SE": [-10.57, -37.45], "TO": [-10.25, -48.30]
        }
        
        df_map_scatter = df_map_choropleth.copy()
        df_map_scatter["lat"] = df_map_scatter["UF"].map(lambda x: coordenadas_estados.get(x, [None, None])[0])
        df_map_scatter["lon"] = df_map_scatter["UF"].map(lambda x: coordenadas_estados.get(x, [None, None])[1])
        
        fig_scatter = px.scatter_geo(
            df_map_scatter.dropna(subset=['lat', 'lon']),
            lat="lat",
            lon="lon",
            size="Notificações",
            color="Notificações",
            color_continuous_scale="Reds",
            hover_name="UF",
            text="UF",
            size_max=30,
            scope='south america'
        )
        
        for trace in fig_scatter.data:
            fig.add_trace(trace)
        
        fig.update_geos(projection_type='mercator', fitbounds='locations',
                       showcoastlines=True, showland=True, landcolor='lightgray',
                       lataxis_range=[-35, 6], lonaxis_range=[-75, -30])
        fig.update_layout(geo=dict(scope='south america'))
        
        fig.update_layout(
            margin={"r":0,"t":50,"l":0,"b":0},
            coloraxis_colorbar=dict(title="Nº de Notificações"),
            coloraxis_showscale=True
        )
        
        return fig.to_html(include_plotlyjs=False, div_id='map-chart')
    
    except Exception as e:
        print(f"Erro ao gerar mapa: {e}")
        return None

def gerar_grafico_correlacao(df_filtrado):
    """Gera heatmap de correlação entre variáveis numéricas."""
    numeric_cols = df_filtrado.select_dtypes(include=['int64', 'float64']).columns
    
    corr_matrix = df_filtrado[numeric_cols].corr()
    
    fig = go.Figure(data=go.Heatmap(z=corr_matrix.values, x=corr_matrix.columns,
                                    y=corr_matrix.columns, colorscale='Viridis'))
    
    fig.update_layout(title='Matriz de Correlação entre Variáveis Numéricas')
    
    return fig.to_html(include_plotlyjs=False, div_id='correlation-chart')

@app.route('/')
def index():
    """Página inicial com visão geral."""
    df = carregar_dados()
    
    if df.empty:
        return render_template('erro.html', mensagem='Nenhum dado disponível')
    
    opcoes_filtro = obter_opcoes_filtro(df)
    metricas = gerar_grafico_metricas(df)
    
    return render_template('index.html',
                         logo_path='logo_hemovigilancia.png',
                         opcoes_filtro=opcoes_filtro,
                         metricas=metricas,
                         ultima_atualizacao=dados_cache['ultima_atualizacao'])

@app.route('/atualizar-dados')
def atualizar_dados():
    """Rota que exibe a tela de carregamento e inicia a atualização via JS."""
    return render_template('atualizando.html')

@app.route('/api/executar-atualizacao')
def executar_atualizacao():
    """API para executar o crawler e atualizar a base de dados em background."""
    global dados_cache
    
    try:
        crawler = HemovigilanciaCrawler(base_path=os.path.join(os.path.dirname(__file__), 'data'))
        
        novo_caminho_csv = crawler.run()
        
        if novo_caminho_csv:
            dados_cache['df'] = None
            dados_cache['timestamp'] = None
            carregar_dados()
            
            return jsonify({'sucesso': True, 'mensagem': 'Dados atualizados com sucesso!'})
        else:
            return jsonify({'sucesso': False, 'mensagem_erro': 'O crawler não conseguiu baixar o novo arquivo.'})
            
    except Exception as e:
        print(f"Erro ao atualizar dados: {e}")
        return jsonify({'sucesso': False, 'mensagem_erro': str(e)})


@app.route('/visao-geral')
def visao_geral():
    """Página de visão geral com métricas e tendências."""
    df = carregar_dados()
    
    if df.empty:
        return jsonify({'erro': 'Nenhum dado disponível'}), 400
    
    filtros = request.args.to_dict(flat=False)
    filtros = {k: v[0].split(',') if v[0] else [] for k, v in filtros.items() if v}
    
    df_filtrado = aplicar_filtros(df, filtros)
    metricas = gerar_grafico_metricas(df_filtrado)
    timeline = gerar_grafico_timeline(df_filtrado)
    
    return render_template('visao_geral.html',
                         metricas=metricas,
                         timeline=timeline,
                         logo_path='logo_hemovigilancia.png')

@app.route('/distribuicoes')
def distribuicoes():
    """Página de distribuições e análises."""
    df = carregar_dados()
    
    if df.empty:
        return jsonify({'erro': 'Nenhum dado disponível'}), 400
    
    filtros = request.args.to_dict(flat=False)
    filtros = {k: v[0].split(',') if v[0] else [] for k, v in filtros.items() if v}
    
    df_filtrado = aplicar_filtros(df, filtros)
    
    grafico_uf = gerar_grafico_distribuicao_uf(df_filtrado)
    grafico_tipo = gerar_grafico_distribuicao_tipo(df_filtrado)
    
    return render_template('distribuicoes.html',
                         grafico_uf=grafico_uf,
                         grafico_tipo=grafico_tipo,
                         logo_path='logo_hemovigilancia.png')

@app.route('/mapa-brasil')
def mapa_brasil():
    """Página com mapa interativo do Brasil."""
    df = carregar_dados()
    
    if df.empty:
        return jsonify({'erro': 'Nenhum dado disponível'}), 400
    
    filtros = request.args.to_dict(flat=False)
    filtros = {k: v[0].split(',') if v[0] else [] for k, v in filtros.items() if v}
    
    df_filtrado = aplicar_filtros(df, filtros)
    mapa = gerar_mapa_brasil(df_filtrado)
    
    return render_template('mapa_brasil.html',
                         mapa=mapa,
                         logo_path='logo_hemovigilancia.png')

@app.route('/correlacao')
def correlacao():
    """Página de análise de correlação."""
    df = carregar_dados()
    
    if df.empty:
        return jsonify({'erro': 'Nenhum dado disponível'}), 400
    
    filtros = request.args.to_dict(flat=False)
    filtros = {k: v[0].split(',') if v[0] else [] for k, v in filtros.items() if v}
    
    df_filtrado = aplicar_filtros(df, filtros)
    grafico_correlacao = gerar_grafico_correlacao(df_filtrado)
    
    return render_template('correlacao.html',
                         grafico_correlacao=grafico_correlacao,
                         logo_path='logo_hemovigilancia.png')

@app.route('/dados')
def dados():
    """Página de acesso aos dados brutos."""
    df = carregar_dados()
    
    if df.empty:
        return render_template('dados.html', dados=[], colunas=[], logo_path='logo_hemovigilancia.png')
    
    filtros = request.args.to_dict(flat=False)
    filtros = {k: v[0].split(',') if v[0] else [] for k, v in filtros.items() if v}
    
    df_filtrado = aplicar_filtros(df, filtros)

    colunas_remover = ['anomalias', 'ANO', 'MES']
    colunas_exibir = [col for col in df_filtrado.columns.tolist() if col not in colunas_remover]
    
    df_display = df_filtrado[colunas_exibir].head(1000)
    
    return render_template('dados.html',
                         dados=df_display.to_dict('records'),
                         colunas=colunas_exibir,
                         total_registros=len(df_filtrado),
                         logo_path='logo_hemovigilancia.png')

@app.route('/dados/maximizar')
def dados_maximizar():
    """Página de maximização de dados brutos."""
    df = carregar_dados()
    
    if df.empty:
        return render_template('dados_maximizar.html', dados=[], colunas=[], logo_path='logo_hemovigilancia.png')

    filtros = request.args.to_dict(flat=False)
    filtros = {k: v[0].split(',') if v[0] else [] for k, v in filtros.items() if v}
    
    df_filtrado = aplicar_filtros(df, filtros)
    
    colunas_remover = ['anomalias', 'ANO', 'MES']
    colunas_exibir = [col for col in df_filtrado.columns.tolist() if col not in colunas_remover]

    df_display = df_filtrado[colunas_exibir].head(5000)
    
    return render_template('dados_maximizar.html',
                         dados=df_display.to_dict('records'),
                         colunas=colunas_exibir,
                         total_registros=len(df_filtrado),
                         logo_path='logo_hemovigilancia.png')


@app.route('/api/filtros')
def api_filtros():
    """API para obter opções de filtros."""
    df = carregar_dados()
    opcoes = obter_opcoes_filtro(df)
    return jsonify(opcoes)

@app.route('/api/dados-filtrados', methods=['POST'])
def api_dados_filtrados():
    """API para obter dados filtrados em JSON."""
    df = carregar_dados()
    
    if df.empty:
        return jsonify({'erro': 'Nenhum dado disponível'}), 400
    
    filtros = request.get_json() or {}
    df_filtrado = aplicar_filtros(df, filtros)
    
    return jsonify({
        'total': len(df_filtrado),
        'dados': df_filtrado.head(100).to_dict('records')
    })

@app.route('/api/exportar-csv')
def api_exportar_csv():
    """API para exportar dados filtrados como CSV."""
    df = carregar_dados()
    
    if df.empty:
        return jsonify({'erro': 'Nenhum dado disponível'}), 400
    
    filtros = request.args.to_dict(flat=False)
    filtros = {k: v[0].split(',') if v[0] else [] for k, v in filtros.items() if v}
    
    df_filtrado = aplicar_filtros(df, filtros)
    csv_data = df_filtrado.to_csv(index=False, sep=';', encoding='ISO-8859-1')
    
    return csv_data, 200, {
        'Content-Disposition': 'attachment; filename=hemovigilancia_exportado.csv',
        'Content-Type': 'text/csv; charset=ISO-8859-1'
    }

@app.route('/api/status')
def api_status():
    """API para verificar o status da aplicação."""
    df = carregar_dados()
    return jsonify({
        'status': 'ok' if not df.empty else 'erro',
        'ultima_atualizacao': dados_cache['ultima_atualizacao'],
        'total_registros': len(df)
    })

if __name__ == '__main__':
    carregar_dados()
    app.run(debug=True)
