# 🩸 Projeto de Hemovigilância — Análise e Dashboard Interativo

Este projeto tem como objetivo analisar notificações de **Hemovigilância em Pós-Mercado**, identificando **padrões, anomalias e tendências regionais** relacionadas à segurança transfusional para o Trabalho de Conclusão de Curso em Bacharelado em Sistemas de Informação.

## 1. Introdução

Este projeto consiste em um Dashboard interativo desenvolvido em Python (Flask) para a análise e visualização de dados de Hemovigilância, com foco em notificações por Estado no Brasil. O objetivo é fornecer uma ferramenta analítica robusta, com filtros dinâmicos, para auxiliar na exploração de tendências, distribuições e correlações nos dados.

## 2. Funcionalidades Principais

### 1. Menu Lateral de Navegação
- **Visão Geral**: Métricas principais e tendências temporais
- **Distribuições**: Análises por região, tipo de evento e período
- **Mapa Brasil**: Visualização geográfica interativa das notificações
- **Correlação**: Análises comparativas entre variáveis
- **Dados**: Acesso direto às tabelas e filtros detalhados

### 2. Sistema de Filtros Dinâmicos
- Filtrar por Estados (UF)
- Filtrar por Tipo de Evento
- Filtrar por Anos
- Aplicação automática de filtros em tempo real
- Restauração de filtros via URL

### 3. Funcionalidade Crawler
- Download automático de dados atualizados
- Integração com o portal dados.gov.br
- Atualização contínua da base de dados
- Sincronização de novos registros

### 4. Visualizações Interativas
- Gráficos de tendência temporal
- Distribuição por UF e tipo de evento
- Mapa interativo do Brasil com dados geográficos
- Matriz de correlação entre variáveis
- Tabelas de dados filtráveis

### 5. Exportação de Dados
- Exportação em formato CSV
- Dados filtrados conforme seleção do usuário
- Download direto do navegador

## 3. Tecnologias Utilizadas

O projeto é construído sobre uma pilha de tecnologias Python e Web, garantindo um ambiente de desenvolvimento eficiente e uma interface de usuário rica.

| Categoria | Tecnologia | Uso no Projeto |
| :--- | :--- | :--- |
| **Backend/Web** | **Python** | Linguagem principal de desenvolvimento. |
| **Backend/Web** | **Flask** | Micro-framework para roteamento e construção do servidor web. |
| **Análise de Dados** | **Pandas** | Manipulação, limpeza e processamento de dados do CSV. |
| **Visualização** | **Plotly** | Geração de gráficos interativos (Mapas, Séries Temporais, Distribuições). |
| **Frontend/Design** | **HTML5/CSS3** | Estrutura e estilização da interface. |
| **Frontend/Design** | **Bootstrap 5** | Framework CSS para responsividade e componentes de UI. |
| **Frontend/Interatividade** | **JavaScript/AJAX** | Lógica de filtros, interações e comunicação assíncrona com o servidor. |

## 4. Como Executar o Projeto

Siga os passos abaixo para configurar e executar a aplicação em seu ambiente local Vscode ou IntelliJ.

### 4.1. Pré-requisitos

Certifique-se de ter o **Python 3** e o **pip** (gerenciador de pacotes do Python) instalados em seu sistema.

### 4.2. Configuração do Ambiente

1.  **Navegue até o diretório do projeto:**
    ```bash
    cd /caminho/para/o/projeto
    ```

2.  **Crie e ative um ambiente virtual (Recomendado):**
    ```bash
    # Cria o ambiente virtual
    python3 -m venv venv

    # Ativa o ambiente virtual (Linux/macOS)
    source venv/bin/activate

    # Ativa o ambiente virtual (Windows - PowerShell)
    # .\venv\Scripts\Activate.ps1
    ```

3.  **Instale as dependências:**
    O projeto utiliza as bibliotecas listadas no arquivo `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

### 4.3. Execução da Aplicação

1.  **Inicie o servidor Flask:**
    ```bash
    python3 app_hemovigilancia.py
    ```

2.  **Acesse o Dashboard:**
    Após a execução, o terminal exibirá o endereço local. Abra seu navegador e acesse:
    ```
    http://127.0.0.1:5000
    ```

## 5. Funcionalidade do Crowler

O arquivo `crawler_hemovigilancia.py` automatiza a atualização de dados:

### Executar Manualmente
```bash
python3 crawler_hemovigilancia.py
```

### Agendar Execução (Linux/Mac)
Adicione à crontab para executar diariamente às 2 da manhã:
```bash
crontab -e
# Adicione a linha:
0 2 * * * cd /caminho/para/HEMOVIGILANCIA && python3 crawler_hemovigilancia.py
```

### Agendar Execução (Windows)
Use o Agendador de Tarefas do Windows para executar o script em intervalos regulares.

## 6. Estrutura do Projeto

A estrutura de arquivos segue o padrão de aplicações Flask:

```
.
├── analise_hemovigilancia.py
├── analise_hemovigilancia_avancado.py
├── app_hemovigilancia.py       # Ponto de entrada da aplicação (rotas e lógica Flask)
├── config.py
├── crawler_hemovigilancia.py
├── dashboard_hemovigilancia.py
├── data/                       # Contém os arquivos de dados (CSV, GeoJSON)
├── data_processor.py
├── LICENSE
├── logo_hemovigilancia.png
├── README.MD
├── README_APP.md               # Este arquivo
├── requirements.txt            # Lista de dependências Python
├── static/                     # Arquivos estáticos (CSS, JS, Imagens)
│   ├── css/
│   ├── images/
│   └── js/
└── templates/                  # Arquivos HTML (Jinja2)
    ├── base.html               # Layout principal com barra lateral e filtros
    ├── correlacao.html
    ├── dados.html
    ├── ...
---
```
Desenvolvido por **Wallace Santos** e Orientado pelo **Tassio Serqueira**
