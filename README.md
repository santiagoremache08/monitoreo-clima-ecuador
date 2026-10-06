# 🇪🇨 Clima y Riesgo - Ecuador

> Centro de Monitoreo Climático y de Riesgos en tiempo real, impulsado por Ciencia de Datos y Procesamiento de Lenguaje Natural (NLP).

## Descripción del Proyecto
Clima y Riesgo Ecuador es una plataforma analítica y de monitoreo descentralizado diseñada para cruzar condiciones meteorológicas en vivo con noticias de última hora. El sistema utiliza Inteligencia Artificial (NER con `spaCy`) para extraer, clasificar y geolocalizar reportes de emergencias e incidentes climáticos, ofreciendo una perspectiva rápida y basada en datos.

---

## Características Principales
- Telemetría en Vivo: Integración con la API de *Open-Meteo* para consultar temperatura, precipitación, humedad y viento de las principales provincias del Ecuador.
- Radar de Alertas (NLP): Extracción automatizada de noticias mediante feeds RSS y análisis de entidades nombradas para ubicar incidentes en el mapa.
- Diseño Dual Inteligente: Visualización en capas con desplazamiento de coordenadas para evitar la superposición de marcadores entre el clima y las alertas.
- Interfaz Adaptativa: Panel de control limpio y sobrio organizado en pestañas interactivas y filtros operativos.

---

## Tecnologías y Librerías
El proyecto está desarrollado íntegramente en Python:
* Streamlit: Construcción y despliegue del panel web interactivo.
* Folium / Streamlit-Folium: Renderización de mapas geoespaciales interactivos.
* spaCy: Procesamiento de Lenguaje Natural (NLP) para la detección de ubicaciones en titulares de noticias.
* Pandas & Requests: Manipulación de estructuras de datos y consumo de APIs meteorológicas.
* GitHub Actions: Automatización de la ejecución diaria del pipeline de extracción de datos.

---

## Enlace a la Aplicación
Puedes acceder a la versión en producción desplegada en Streamlit Cloud a través del siguiente enlace:
[Ver Aplicación en Vivo](https://monitoreo-clima-ecuador-rlj9qualfsnv3xascwaeqn.streamlit.app/#panel-de-monitoreo-de-clima-y-emergencias)

---

## Estructura del Repositorio
```text
├── .github/workflows/   # Automatización del pipeline diario (GitHub Actions)
├── data/                # Archivos CSV generados con los incidentes procesados
├── app.py               # Código principal del panel de control (Streamlit)
├── pipeline_sgr.py      # Script de extracción NLP y geolocalización
└── requirements.txt     # Dependencias del proyecto
