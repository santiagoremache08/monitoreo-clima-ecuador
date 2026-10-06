
import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import time

# 1. Configuración de la página
st.set_page_config(page_title="Monitoreo en Tiempo Real", layout="wide")

# 2. Inyección de CSS general
st.markdown(
    """
    <style>
    html, body, p, div, span, label, li, td, th { font-size: 13px !important; }
    h1 { font-size: 28px !important; }
    h2 { font-size: 22px !important; }
    h3 { font-size: 18px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔴 Monitoreo Actual de Lluvias en Ecuador")
st.markdown("Datos obtenidos en tiempo real. Nivel de riesgo calculado por la intensidad de precipitación actual.")

# 3. Diccionario de coordenadas
provincias_ec = {
    'Azuay': (-2.9001, -79.0059), 'Bolívar': (-1.5916, -79.0022),
    'Cañar': (-2.7397, -78.8486), 'Carchi': (0.8119, -77.7173),
    'Chimborazo': (-1.6669, -78.6471), 'Cotopaxi': (-0.9328, -78.6155),
    'El Oro': (-3.2581, -79.9553), 'Esmeraldas': (0.9592, -79.6539),
    'Galápagos': (-0.9006, -89.6111), 'Guayas': (-2.1961, -79.8862),
    'Imbabura': (0.3392, -78.1222), 'Loja': (-3.9931, -79.2042),
    'Los Ríos': (-1.8022, -79.5344), 'Manabí': (-1.0545, -80.4544),
    'Morona Santiago': (-2.3087, -78.1114), 'Napo': (-0.9898, -77.8159),
    'Orellana': (-0.4663, -76.9871), 'Pastaza': (-1.4837, -77.9954),
    'Pichincha': (-0.2299, -78.5249), 'Santa Elena': (-2.2262, -80.8587),
    'Santo Domingo': (-0.2530, -79.1754), 'Sucumbíos': (0.0860, -76.8793),
    'Tungurahua': (-1.2417, -78.6233), 'Zamora Chinchipe': (-4.0692, -78.9567)
}

# 4. Función de extracción de datos
@st.cache_data(ttl=600)
def obtener_datos_en_vivo():
    datos_actuales = []
    for provincia, (lat, lon) in provincias_ec.items():
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation,temperature_2m,relative_humidity_2m,wind_speed_10m&timezone=America%2FGuayaquil"
        try:
            respuesta = requests.get(url).json()
            precipitacion = respuesta['current']['precipitation']
            temperatura = respuesta['current']['temperature_2m']
            humedad = respuesta['current']['relative_humidity_2m']
            viento = respuesta['current']['wind_speed_10m']
            
            riesgo = 'Bajo'
            if precipitacion > 10:
                riesgo = 'Alto'
            elif precipitacion > 2:
                riesgo = 'Medio'
                
            datos_actuales.append({
                'Provincia': provincia, 'Latitud': lat, 'Longitud': lon,
                'Precipitacion_Actual_mm': precipitacion, 'Temperatura_C': temperatura,
                'Humedad_Pct': humedad, 'Viento_kmh': viento, 'Riesgo_Inmediato': riesgo
            })
        except:
            pass 
        time.sleep(0.1)
    return pd.DataFrame(datos_actuales)

df_vivo = obtener_datos_en_vivo()

# 5. Filtros y Métricas
st.sidebar.header("Filtros en Vivo")
mostrar_solo_lluvia = st.sidebar.checkbox("Mostrar solo provincias con lluvia actual", value=False)

if mostrar_solo_lluvia and not df_vivo.empty:
    df_vivo = df_vivo[df_vivo['Precipitacion_Actual_mm'] > 0]

col1, col2, col3 = st.columns(3)
col1.metric("Provincias Analizadas", len(df_vivo))
col2.metric("Provincias con Lluvia Activa", len(df_vivo[df_vivo['Precipitacion_Actual_mm'] > 0]) if not df_vivo.empty else 0)
col3.metric("Riesgo Alto Detectado", len(df_vivo[df_vivo['Riesgo_Inmediato'] == 'Alto']) if not df_vivo.empty else 0)

# 6. Construcción del Mapa
mapa_ecuador = folium.Map(location=[-1.8312, -78.1834], zoom_start=6)

for _, fila in df_vivo.iterrows():
    # Paleta de colores para el riesgo
    color_hex = "#d32f2f" if fila['Riesgo_Inmediato'] == 'Alto' else "#f57c00" if fila['Riesgo_Inmediato'] == 'Medio' else "#388e3c"
    radio = 12 + (fila['Precipitacion_Actual_mm'] * 2)
    
    # HTML profesional y estructurado en forma de tabla
    html_popup = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 12px; width: 160px;">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #2c3e50; border-bottom: 1px solid #e0e0e0; padding-bottom: 4px;">
            {fila['Provincia']}
        </h4>
        <table style="width: 100%; border-collapse: collapse; color: #444;">
            <tr>
                <td style="padding: 3px 0;">🌧️ Lluvia:</td>
                <td style="text-align: right;"><b>{fila['Precipitacion_Actual_mm']} mm</b></td>
            </tr>
            <tr>
                <td style="padding: 3px 0;">🌡️ Temp:</td>
                <td style="text-align: right;"><b>{fila['Temperatura_C']} °C</b></td>
            </tr>
            <tr>
                <td style="padding: 3px 0;">💧 Humedad:</td>
                <td style="text-align: right;"><b>{fila['Humedad_Pct']}%</b></td>
            </tr>
            <tr>
                <td style="padding: 3px 0;">🌬️ Viento:</td>
                <td style="text-align: right;"><b>{fila['Viento_kmh']} km/h</b></td>
            </tr>
            <tr>
                <td style="padding: 8px 0 0 0; color: #666;"><b>Riesgo:</b></td>
                <td style="padding: 8px 0 0 0; text-align: right; color: {color_hex};"><b>{fila['Riesgo_Inmediato']}</b></td>
            </tr>
        </table>
    </div>
    """
    
    folium.CircleMarker(
        location=[fila['Latitud'], fila['Longitud']],
        radius=radio, 
        # Envolvemos el HTML en folium.Popup fijando el ancho máximo para evitar desbordes
        popup=folium.Popup(html_popup, max_width=200),
        color=color_hex, fill=True, fill_color=color_hex, fill_opacity=0.7
    ).add_to(mapa_ecuador)

st_folium(mapa_ecuador, width=800, height=500)

# 7. Tabla de datos
st.subheader("Datos de Telemetría")
st.dataframe(df_vivo, use_container_width=True)