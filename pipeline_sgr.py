import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import spacy

# 1. Cargar el modelo NLP en español
try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    print("Descargando modelo spaCy...")
    from spacy.cli import download
    download("es_core_news_sm")
    nlp = spacy.load("es_core_news_sm")

def extraer_alertas_rss():
    print("Consultando el feed de noticias de última hora...")
    # Ampliamos el rango a 7 días y sumamos más términos de búsqueda operativos en Ecuador
    url = "https://news.google.com/rss/search?q=inundacion+OR+deslave+OR+aluvion+OR+lluvias+OR+emergencia+ecuador+when:7d&hl=es-419&gl=US&ceid=US:es-419"
    
    respuesta = requests.get(url)
    soup = BeautifulSoup(respuesta.content, 'xml')
    
    noticias = []
    for item in soup.find_all('item'):
        noticias.append({
            'titulo': item.title.text,
            'fecha': item.pubDate.text,
            'enlace': item.link.text
        })
    return noticias

def procesar_entidades_geograficas(noticias):
    print("Aplicando Reconocimiento de Entidades Nombradas (NER)...")
    
    # Base de coordenadas de referencia para el cruce
    coordenadas_ec = {
        'quito': (-0.2298, -78.5249), 'guayaquil': (-2.1961, -79.8862),
        'cuenca': (-2.9001, -79.0059), 'santo domingo': (-0.2530, -79.1754),
        'machala': (-3.2581, -79.9553), 'manta': (-0.9500, -80.7300), 
        'portoviejo': (-1.0545, -80.4544), 'loja': (-3.9931, -79.2042), 
        'ambato': (-1.2417, -78.6233), 'esmeraldas': (0.9592, -79.6539), 
        'riobamba': (-1.6669, -78.6471), 'ibarra': (0.3392, -78.1222),
        'latacunga': (-0.9328, -78.6155), 'tulcán': (0.8119, -77.7173),
        'baños': (-1.3964, -78.4247), 'alausí': (-2.2015, -78.8472),
        'pichincha': (-0.2298, -78.5249), 'azuay': (-2.9001, -79.0059),
        'guayas': (-2.1961, -79.8862), 'manabí': (-1.0545, -80.4544)
    }
    
    eventos = []
    for noti in noticias:
        doc = nlp(noti['titulo'])
        # Extraer solo palabras clasificadas como Localización (LOC)
        lugares_detectados = [ent.text.lower() for ent in doc.ents if ent.label_ == 'LOC']
        
        # Respaldo: Búsqueda directa si el modelo NLP duda
        if not lugares_detectados:
            lugares_detectados = [lugar for lugar in coordenadas_ec.keys() if lugar in noti['titulo'].lower()]
            
        for loc in lugares_detectados:
            for lugar_conocido, (lat, lon) in coordenadas_ec.items():
                if lugar_conocido in loc:
                    eventos.append({
                        'Provincia': loc.title(),
                        'Canton': loc.title(),
                        'Latitud': lat,
                        'Longitud': lon,
                        'Fecha': noti['fecha'],
                        'Afectacion': noti['titulo'], 
                        'Estado_Via': 'Alerta en Medios',
                        'Enlace': noti['enlace']      
                    })
                    break 
                    
    df = pd.DataFrame(eventos)
    if not df.empty:
        # Eliminar duplicados basados en el enlace de la noticia
        df = df.drop_duplicates(subset=['Enlace'])
    return df

if __name__ == "__main__":
    noticias_crudas = extraer_alertas_rss()
    
    if noticias_crudas:
        df_nuevo = procesar_entidades_geograficas(noticias_crudas)
        
        if not df_nuevo.empty:
            if not os.path.exists('data'):
                os.makedirs('data')
            
            ruta_csv = 'data/deslaves_sgr.csv'
            
            # Si ya existe un archivo previo, combinamos para acumular histórico sin repetir
            if os.path.exists(ruta_csv):
                df_antiguo = pd.read_csv(ruta_csv)
                df_final = pd.concat([df_nuevo, df_antiguo]).drop_duplicates(subset=['Enlace'])
            else:
                df_final = df_nuevo
                
            df_final.to_csv(ruta_csv, index=False)
            print(f"✅ Pipeline exitoso. Total de incidentes acumulados: {len(df_final)}")
        else:
            print("⚠️ No se encontraron ubicaciones extraíbles en las noticias recientes.")
    else:
        print("Tranquilidad: No se registran noticias de emergencias en el periodo consultado.")
