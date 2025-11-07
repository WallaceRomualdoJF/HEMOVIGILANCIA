import pandas as pd
import requests
import os
import zipfile
from io import StringIO, BytesIO
from datetime import datetime

class HemovigilanciaCrawler:

    URL_DADOS_CSV = "https://dados.anvisa.gov.br/dados/DADOS_ABERTOS_HEMOVIGILANCIA.csv"
    CAMINHO_DADOS_ORIGINAL = "DADOS_ABERTOS_HEMOVIGILANCIA_UTF8.csv"
    
    def __init__(self, base_path='data'):

        self.base_path = base_path
        self.full_path = os.path.join(self.base_path, self.CAMINHO_DADOS_ORIGINAL)
        
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _baixar_dados_atuais(self):
        print(f"Iniciando o download dos dados de: {self.URL_DADOS_CSV}")
        try:

            response = requests.get(self.URL_DADOS_CSV, verify=False, timeout=60) 
            response.raise_for_status()
            
            content = response.content.decode('ISO-8859-1')
            df_novo = pd.read_csv(StringIO(content), sep=';', on_bad_lines='skip')
            
            print("Download e leitura do novo arquivo concluídos com sucesso.")
            return df_novo
        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar os dados: {e}")
            raise Exception(f"Erro de rede/HTTP ao baixar os dados: {e}")
        except Exception as e:
            print(f"Erro ao processar o arquivo CSV: {e}")
            raise Exception(f"Erro ao processar o CSV: {e}")

    def _integrar_dados(self, df_novo):
        """Salva o novo DataFrame, substituindo o arquivo existente."""
        if df_novo is None or df_novo.empty:
            print("Nenhum dado novo para salvar.")
            return False

        try:
            df_novo.to_csv(self.full_path, sep=';', encoding='ISO-8859-1', index=False)
            print(f"Dados atualizados e salvos em {self.full_path}")
            return True
        except Exception as e:
            print(f"Erro ao salvar o arquivo atualizado: {e}")
            raise Exception(f"Erro ao salvar o arquivo: {e}")

    def run(self):
        print(f"--- Executando HemovigilanciaCrawler em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        try:
            df_novo = self._baixar_dados_atuais()
            
            if self._integrar_dados(df_novo):
                print("Crawler concluído com sucesso. Dados de hemovigilância atualizados.")
                return self.full_path
            else:
                print("Crawler falhou ao atualizar os dados.")
                return None
        except Exception as e:
            print(f"Erro fatal no Crawler: {e}")
            return None

if __name__ == "__main__":
    crawler = HemovigilanciaCrawler(base_path=os.path.join(os.path.dirname(__file__), 'data'))
    crawler.run()
