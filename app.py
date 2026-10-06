import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import os

# Configuración de la página
st.set_page_config(page_title="Monitoreo Clima Ecuador", layout="wide")

# Coordenadas base de las provincias
PROVINCIAS = {
    'Azuay': (-2.9001, -79.0059), 'Bolívar': (-1.5916, -79.0022), 'Cañar': (-2.7397, -78.8486),
    'Carchi': (0.8119, -77.7173), 'Chimborazo': (-1.6669, -78.6471), 'Cotopaxi': (-0.9328, -78.6155),
    'El Oro': (-3.2581, -79.9553), 'Esmeraldas': (0.9592, -79.6539), 'Galápagos': (-0.9006, -89.6111),
    'Guayas': (-2.1961, -79.8862), 'Imbabura': (0.3392, -78.1222), 'Loja': (-3.9931, -79.2042),
    'Los Ríos': (-1.4424, -79.4661), 'Manabí': (-1.0545, -80.4544), 'Morona Santiago': (-2.3087, -78.1147),
    'Napo': (-0.9336, -77.8105), 'Orellana': (-0.9416, -76.9928), 'Pastaza': (-1.4883, -77.8541),
    'Pichincha': (-0.2298, -78.5249), 'Santa Elena': (-2.2262, -80.8587), 'Santo Domingo': (-0.2530, -79.1754),
    'Sucumbíos': (-0.0860, -76.8838), 'Tungurahua': (-1.2417, -78.6233), 'Zamora Chinchipe': (-4.0692, -78.9567)
}

@st.cache_data(ttl=600)
def obtener_clima_vivo():
    datos = []
    for prov, (lat, lon) in PROVINCIAS.items():
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&timezone=America%2FGuayaquil"
            res = requests.get(url).json()
            precip = res['current']['precipitation']
            riesgo = 'Alto' if precip > 10 else 'Medio' if precip > 2 else 'Bajo'
            
            datos.append({
                'Provincia': prov, 'Latitud': lat, 'Longitud': lon,
                'Precipitacion_Actual_mm': precip,
                'Temperatura_C': res['current']['temperature_2m'],
                'Humedad_Pct': res['current']['relative_humidity_2m'],
                'Viento_kmh': res['current']['wind_speed_10m'],
                'Riesgo_Inmediato': riesgo
            })
        except:
            pass
    return pd.DataFrame(datos)

@st.cache_data(ttl=60)
def obtener_incidentes():
    ruta = "data/deslaves_sgr.csv"
    if os.path.exists(ruta):
        return pd.read_csv(ruta)
    return pd.DataFrame()

# ==========================================
# INTERFAZ DE USUARIO Y BARRA LATERAL
# ==========================================

# Barra lateral (Filtros y Leyenda)
with st.sidebar:
    st.markdown("### 🎛️ Controles del Tablero")
    solo_lluvia = st.checkbox("🌧️ Mostrar solo zonas con lluvia actual")
    
    # Nuevo complemento: Slider para filtrar por intensidad
    lluvia_minima = st.slider("💧 Lluvia mínima (mm)", min_value=0.0, max_value=20.0, value=0.0, step=0.5)
    
    st.markdown("---")
    
    # Nuevo complemento: Leyenda del mapa
    st.markdown("### 📖 Leyenda")
    st.markdown("🟢 **Riesgo Bajo:** < 2 mm")
    st.markdown("🟠 **Riesgo Medio:** 2 - 10 mm")
    st.markdown("🔴 **Riesgo Alto:** > 10 mm")
    st.markdown("🚨 **Pin Rojo:** Alerta en Medios")

st.markdown("### 📡 Panel de Monitoreo de Clima y Emergencias")
st.markdown("Datos obtenidos en tiempo real. Nivel de riesgo calculado por la intensidad de precipitación actual.")

# Carga de DataFrames
df_clima = obtener_clima_vivo()
df_incidentes = obtener_incidentes()

# Aplicar los nuevos filtros de la barra lateral
df_mostrar = df_clima[df_clima['Precipitacion_Actual_mm'] >= lluvia_minima]
if solo_lluvia:
    df_mostrar = df_mostrar[df_mostrar['Precipitacion_Actual_mm'] > 0]

# Métricas superiores
col1, col2, col3 = st.columns(3)
col1.metric("Provincias en Pantalla", len(df_mostrar))
col2.metric("Provincias con Lluvia Activa", len(df_clima[df_clima['Precipitacion_Actual_mm'] > 0]))
col3.metric("Riesgo Alto Detectado", len(df_clima[df_clima['Riesgo_Inmediato'] == 'Alto']))

# Inicializar Mapa
mapa = folium.Map(location=[-1.83, -78.18], zoom_start=6)

# CAPA 1: Clima (Ahora con tarjetas HTML de telemetría completa)
for _, fila in df_mostrar.iterrows():
    color = "#d32f2f" if fila['Riesgo_Inmediato'] == 'Alto' else "#f57c00" if fila['Riesgo_Inmediato'] == 'Medio' else "#388e3c"
    
    # Tarjeta de clima con CSS
    html_clima = f"""
    <div style="font-family: 'Segoe UI', sans-serif; width: 160px;">
        <b style="font-size: 15px; color: #111827;">{fila['Provincia']}</b><br>
        <hr style="margin: 6px 0; border: 0; border-top: 1px solid #e5e7eb;">
        🌧️ <b>Lluvia:</b> {fila['Precipitacion_Actual_mm']} mm<br>
        🌡️ <b>Temp:</b> {fila['Temperatura_C']} °C<br>
        💧 <b>Humedad:</b> {fila['Humedad_Pct']}%<br>
        💨 <b>Viento:</b> {fila['Viento_kmh']} km/h<br>
        <hr style="margin: 6px 0; border: 0; border-top: 1px solid #e5e7eb;">
        <b>Riesgo:</b> <span style="color: {color}; font-weight: bold;">{fila['Riesgo_Inmediato']}</span>
    </div>
    """
    
    folium.CircleMarker(
        location=[fila['Latitud'], fila['Longitud']],
        radius=8 + (fila['Precipitacion_Actual_mm'] * 2),
        color=color, fill=True, fill_color=color, fill_opacity=0.6,
        popup=folium.Popup(html_clima, max_width=200)
    ).add_to(mapa)

# CAPA 2: Incidentes detectados por NLP (Pines Rojos con Diseño Profesional)
if not df_incidentes.empty:
    for _, fila in df_incidentes.iterrows():
        if pd.notna(fila.get('Latitud')) and pd.notna(fila.get('Longitud')):
            afectacion = fila.get('Afectacion', 'Detalle no disponible')
            enlace = fila.get('Enlace', '#')
            provincia = fila.get('Provincia', 'Ubicación')
            
            # Tarjeta profesional con CSS integrado
            html_tarjeta = f"""
            <div style="font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; width: 260px; padding: 5px;">
                <div style="background-color: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">
                    🚨 Alerta Activa
                </div>
                <h4 style="margin: 0 0 8px 0; color: #111827; font-size: 16px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px;">
                    {provincia}
                </h4>
                <p style="margin: 0 0 15px 0; color: #4b5563; font-size: 13px; line-height: 1.5;">
                    {afectacion}
                </p>
                <a href="{enlace}" target="_blank" style="display: block; text-align: center; background-color: #2563eb; color: white; padding: 8px 12px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 500; box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);">
                    Leer fuente oficial ↗
                </a>
            </div>
            """
            
            folium.Marker(
                location=[fila['Latitud'], fila['Longitud']],
                icon=folium.Icon(color="red", icon="warning-sign"),
                popup=folium.Popup(html_tarjeta, max_width=320)
            ).add_to(mapa)

# Renderizar Mapa
st_folium(mapa, width=1000, height=500)

# Tabla Inferior
st.markdown("### Datos de Telemetría")
st.dataframe(df_mostrar.drop(columns=['Latitud', 'Longitud']), use_container_width=True)
