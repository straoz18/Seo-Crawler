# --- COMIENZO DEL CÓDIGO A AÑADIR/MODIFICAR ---
import streamlit as st # <--- ¡ESTA DEBE SER LA PRIMERA LÍNEA!
import requests
from bs4 import BeautifulSoup
import pandas as pd
from google import genai
from google.genai import types

# Inicializa el cliente de Gemini usando la clave de los secretos de Streamlit
# Esto debe ir al inicio del script, junto a los otros imports
try:
    # Intenta obtener la clave de los secretos de Streamlit
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_KEY)
except (KeyError, AttributeError):
    # Si la clave no está disponible (ej. si estás probando localmente), avisa.
    st.error("Error: La clave GEMINI_API_KEY no está configurada en los secretos de Streamlit.")
    client = None

# --- Función de IA para reescribir metadatos ---

def generate_seo_suggestions(title, meta_desc, content_text):
    if not client:
        return "IA no disponible (Clave de API no configurada)."

    prompt = f"""
    Eres un experto en SEO con 10 años de experiencia. Tu tarea es analizar los siguientes metadatos y contenido de una página web y proponer optimizaciones que mejoren el Click-Through Rate (CTR) en los resultados de búsqueda.

    --- Datos de la página ---
    Título actual: {title}
    Meta Description actual: {meta_desc}
    Contenido principal (Fragmento): {content_text[:1000]} 

    --- Tarea ---
    1. Propón 1 Título SEO mejorado (menos de 60 caracteres) con un foco claro en palabras clave y CTR.
    2. Propón 1 Meta Description optimizada (menos de 150 caracteres) que sea un llamado a la acción persuasivo y que use palabras clave del texto.

    Formatea tu respuesta de la siguiente manera:
    TÍTULO PROPUESTO: [Tu nuevo título]
    META DESCRIPTION PROPUESTA: [Tu nueva descripción]
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Rápido y eficiente para esta tarea
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Error en la API de Gemini: {e}"

# --- MODIFICACIÓN DE LA FUNCIÓN analyze_page ---

# DEBES LLAMAR A LA NUEVA FUNCIÓN DENTRO DE analyze_page

def analyze_page(url):
    # ... (Todo el código de extracción de datos existente) ...
    # ... (Obtienes title, meta_desc_content, text_content) ...

    # **AGREGA ESTA SECCIÓN AL FINAL DE analyze_page ANTES DEL RETURN**
    
    # Llama a la IA para obtener sugerencias
    if response.status_code == 200 and len(text_content) > 50:
        ia_suggestions = generate_seo_suggestions(title, meta_desc_content, text_content)
    else:
        ia_suggestions = "No se puede analizar (Página vacía o error)."

    return {
        "URL": url,
        "Status": response.status_code,
        "Title": title,
        # ... (Otros campos existentes) ...
        "Audit Flags": ", ".join(audit_notes) if audit_notes else "✅ Óptimo",
        # **AÑADE ESTE NUEVO CAMPO AL DICCIONARIO DE RETORNO**
        "IA Suggestions": ia_suggestions 
    }
