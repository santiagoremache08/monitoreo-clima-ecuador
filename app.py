import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Centro de Monitoreo | Clima y Riesgo Ecuador", layout="wide")

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

@st.cache_data(ttl=600, show_spinner=False)
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

@st.cache_data(ttl=60, show_spinner=False)
def obtener_incidentes():
    ruta = "data/deslaves_sgr.csv"
    if os.path.exists(ruta):
        return pd.read_csv(ruta)
    return pd.DataFrame()

# ==========================================
# BARRA LATERAL (SOBRIA CON GUIAS VISUALES)
# ==========================================
with st.sidebar:
    st.markdown("### 🇪🇨 Clima y Riesgo - Ecuador")
    st.markdown("Panel de Control Operativo")
    st.markdown("---")
    
    filtro_riesgo = st.radio(
        "Filtrar Vista del Mapa",
        [
            "🌍 Mostrar Todo", 
            "🌧️ Solo Lluvia Activa", 
            "⚠️ Riesgo Medio y Alto", 
            "🚨 Solo Riesgo Alto"
        ]
    )
    
    st.markdown("---")
    if st.button("🔄 Sincronizar Datos"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("#### Descripción General")
    st.markdown(
        "Sistema analítico enfocado en el territorio ecuatoriano que integra telemetría "
        "meteorológica en tiempo real con extracción automatizada de noticias mediante "
        "procesamiento de lenguaje natural (NLP), permitiendo la identificación temprana "
        "de riesgos e incidentes geolocalizados."
    )

# ==========================================
# CABECERA Y METRICAS
# ==========================================
st.title("Centro de Monitoreo Climático y de Riesgos - Ecuador")
hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
st.markdown(f"**Última actualización:** `{hora_actual}` | **Fuentes:** Open-Meteo & RSS NLP")

df_clima = obtener_clima_vivo()
df_incidentes = obtener_incidentes()

# Filtrado de clima
if filtro_riesgo == "🌍 Mostrar Todo":
    df_mostrar = df_clima
elif filtro_riesgo == "🌧️ Solo Lluvia Activa":
    df_mostrar = df_clima[df_clima['Precipitacion_Actual_mm'] > 0]
elif filtro_riesgo == "⚠️ Riesgo Medio y Alto":
    df_mostrar = df_clima[df_clima['Precipitacion_Actual_mm'] >= 2]
elif filtro_riesgo == "🚨 Solo Riesgo Alto":
    df_mostrar = df_clima[df_clima['Precipitacion_Actual_mm'] >= 10]

# Métricas estilizadas
col1, col2, col3, col4 = st.columns(4)
col1.metric("Provincias Analizadas", len(df_clima))
col2.metric("Provincias con Lluvia", len(df_clima[df_clima['Precipitacion_Actual_mm'] > 0]))
col3.metric("Riesgo Alto (Clima)", len(df_clima[df_clima['Riesgo_Inmediato'] == 'Alto']))
col4.metric("Alertas en Medios", len(df_incidentes))

st.markdown("---")

# ==========================================
# CREACIÓN DE PESTAÑAS
# ==========================================
pestana_mapa, pestana_tabla = st.tabs(["🗺️ Mapa Interactivo", "📋 Registros y Telemetría"])

with pestana_mapa:
    # Inicializar Mapa base
    mapa = folium.Map(location=[-1.83, -78.18], zoom_start=6, control_scale=True)

    # CAPA 1: Clima (Círculos)
    for _, fila in df_mostrar.iterrows():
        color = "#d32f2f" if fila['Riesgo_Inmediato'] == 'Alto' else "#f57c00" if fila['Riesgo_Inmediato'] == 'Medio' else "#388e3c"
        
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

    # CAPA 2: Incidentes (Pines Rojos con Desplazamiento Inteligente)
    if not df_incidentes.empty:
        for _, fila in df_incidentes.iterrows():
            lat = fila.get('Latitud')
            lon = fila.get('Longitud')
            
            if pd.notna(lat) and pd.notna(lon):
                lat_desplazada = lat + 0.08
                lon_desplazada = lon + 0.04
                
                afectacion = fila.get('Afectacion', 'Detalle no disponible')
                provincia = fila.get('Provincia', 'Ubicación')
                enlace = fila.get('Enlace', '#')
                
                if pd.isna(enlace) or enlace == '#':
                    html_boton = f"""<div style="text-align: center; color: #6b7280; font-size: 11px; margin-top: 12px; font-style: italic;">Enlace no disponible</div>"""
                else:
                    html_boton = f"""<a href="{enlace}" target="_blank" style="display: block; text-align: center; background-color: #2563eb; color: white; padding: 8px 12px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 500; box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2); margin-top: 10px;">Ver Fuente Original ↗</a>"""
                
                html_tarjeta = f"""
                <div style="font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; width: 260px; padding: 5px;">
                    <div style="background-color: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">
                        🚨 Alerta Activa
                    </div>
                    <h4 style="margin: 0 0 8px 0; color: #111827; font-size: 16px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px;">
                        {provincia}
                    </h4>
                    <p style="margin: 0 0 5px 0; color: #4b5563; font-size: 13px; line-height: 1.5;">
                        {afectacion}
                    </p>
                    {html_boton}
                </div>
                """
                
                folium.Marker(
                    location=[lat_desplazada, lon_desplazada],
                    icon=folium.Icon(color="red", icon="warning-sign"),
                    popup=folium.Popup(html_tarjeta, max_width=320)
                ).add_to(mapa)

    # Renderizar Mapa limpio
    st_folium(mapa, width=1200, height=600)

with pestana_tabla:
    st.markdown("### 📋 Telemetría Meteorológica")
    st.dataframe(df_mostrar.drop(columns=['Latitud', 'Longitud']), use_container_width=True)
    
    if not df_incidentes.empty:
        st.markdown("### 🚨 Alertas Procesadas por IA")
        st.dataframe(df_incidentes, use_container_width=True)
