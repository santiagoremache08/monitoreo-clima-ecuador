import os
import io
import requests
from bs4 import BeautifulSoup
import pandas as pd

def descargar_ultimo_excel_sgr():
    url_portal = "https://www.gestionderiesgos.gob.ec/informes-de-situacion/" 
    
    # 1. Definir el User-Agent para simular un navegador real
    cabeceras = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 2. Enviar la petición usando las cabeceras
    respuesta = requests.get(url_portal, headers=cabeceras)
    soup = BeautifulSoup(respuesta.text, 'html.parser')
    
    enlace_excel = None
    for a in soup.find_all('a', href=True):
        href_lower = a['href'].lower()
        if 'matriz' in href_lower and (href_lower.endswith('.xlsx') or href_lower.endswith('.xls')):
            enlace_excel = a['href']
            break
            
    if not enlace_excel: 
        return None
        
    # 3. También debemos usar las cabeceras para descargar el archivo Excel
    datos_crudos = requests.get(enlace_excel, headers=cabeceras).content
    return pd.read_excel(io.BytesIO(datos_crudos), engine='openpyxl')

def procesar_y_guardar_matriz(df):
    print("Iniciando limpieza de la matriz de eventos...")
    
    # Estandarizar nombres de columnas
    df.columns = df.columns.str.strip().str.upper()
    
    # Filtrar eventos críticos
    eventos_nino = ['DESLIZAMIENTO', 'INUNDACION', 'ALUVION', 'HUNDIMIENTO', 'SOCAVAMIENTO']
    if 'EVENTO' in df.columns:
        df_filtrado = df[df['EVENTO'].isin(eventos_nino)].copy()
    else:
        df_filtrado = df.copy()
    
    # Limpieza espacial
    df_filtrado['LATITUD'] = pd.to_numeric(df_filtrado['LATITUD'], errors='coerce')
    df_filtrado['LONGITUD'] = pd.to_numeric(df_filtrado['LONGITUD'], errors='coerce')
    df_filtrado = df_filtrado.dropna(subset=['LATITUD', 'LONGITUD'])
    
    # Renombrar para Streamlit
    df_final = df_filtrado.rename(columns={
        'PROVINCIA': 'Provincia',
        'CANTÓN': 'Canton',
        'LATITUD': 'Latitud',
        'LONGITUD': 'Longitud',
        'FECHA': 'Fecha',
        'DETALLE': 'Afectacion',
        'ESTADO_VIA': 'Estado_Via'
    })
    
    if 'Estado_Via' not in df_final.columns:
        df_final['Estado_Via'] = 'No especificado'
    if 'Afectacion' not in df_final.columns:
        df_final['Afectacion'] = df_final.get('EVENTO', 'Sin detalle adicional')
        
    # Exportar el CSV para la app web
    if not os.path.exists('data'):
        os.makedirs('data')
        
    ruta_salida = 'data/deslaves_sgr.csv'
    columnas_finales = ['Provincia', 'Canton', 'Latitud', 'Longitud', 'Fecha', 'Afectacion', 'Estado_Via']
    
    df_guardar = df_final[[col for col in columnas_finales if col in df_final.columns]]
    df_guardar.to_csv(ruta_salida, index=False)
    
    print(f"✅ Pipeline finalizado. {len(df_guardar)} eventos limpios guardados en '{ruta_salida}'.")

if __name__ == "__main__":
    dataframe_crudo = descargar_ultimo_excel_sgr()
    
    if dataframe_crudo is not None:
        procesar_y_guardar_matriz(dataframe_crudo)
