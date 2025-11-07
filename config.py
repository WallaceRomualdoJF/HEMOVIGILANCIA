"""
Arquivo de configuração para a aplicação Flask de Hemovigilância
"""

import os
from datetime import timedelta

class Config:
    """Configurações base para a aplicação"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hemovigilancia_secret_key_2025_dev'
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    UPLOAD_FOLDER = 'uploads'
    
    DATA_FOLDER = 'data'
    TEMPLATES_FOLDER = 'templates'
    STATIC_FOLDER = 'static'
    
    DATA_URL = 'https://dados.anvisa.gov.br/dados/DADOS_ABERTOS_HEMOVIGILANCIA.csv'
    
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'app.log'


class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento"""
    
    DEBUG = True
    TESTING = False
    ENV = 'development'
    
    SEND_FILE_MAX_AGE_DEFAULT = 0


class ProductionConfig(Config):
    """Configurações para ambiente de produção"""
    
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    SESSION_COOKIE_SECURE = True
    
    CACHE_DEFAULT_TIMEOUT = 3600
    SEND_FILE_MAX_AGE_DEFAULT = 31536000


class TestingConfig(Config):
    """Configurações para testes"""
    
    DEBUG = True
    TESTING = True
    ENV = 'testing'
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

def get_config(env=None):
    """Retorna a configuração apropriada baseada no ambiente"""
    
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)

CORES = {
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40',
}

ESCALA_CORES_MAPA = 'Reds'

ITEMS_POR_PAGINA = 50
MAX_ITEMS_TABELA = 1000

ALTURA_GRAFICO_PADRAO = 500
LARGURA_GRAFICO_PADRAO = 1000

IDIOMA = 'pt_BR'
TIMEZONE = 'America/Sao_Paulo'

APP_NAME = 'Dashboard Hemovigilância'
APP_VERSION = '1.0.0'
APP_AUTHOR = 'ANVISA'
APP_DESCRIPTION = 'Dashboard interativo de análise de dados de hemovigilância em pós-mercado'

LINKS_UTEIS = {
    'dados_abertos': 'https://dados.gov.br/dados/conjuntos-dados/hemovigilancia-em-pos-mercado',
    'anvisa': 'https://www.gov.br/anvisa/pt-br',
    'hemovigilancia': 'https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa/2022/manual_de_hemovigilancia__dez22-07-12-2022.pdf',
}

