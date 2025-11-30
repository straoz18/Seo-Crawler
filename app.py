import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import time

# Importaciones de la API de Google Gemini (Asegúrate de que 'google-genai' esté en requirements.txt)
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="SEO Audit Tool con IA", layout="wide")

st.title("🕷️ Herramienta de Auditoría y Extracción SEO (Impulsada por IA)")
st.markdown("""
Introduce la URL base y el número máximo de páginas. La IA de Gemini sugerirá optimizaciones de Título y Meta Descripción.
""")

# --- INICIALIZACIÓN Y GESTIÓN DE LA CLAVE DE API ---
# Intenta obtener la clave de los secretos de Streamlit (el archivo .streamlit/secrets.toml)
client = None
try:
    # Verificamos si Streamlit está en modo 'secrets' (deploy)
    if st.secrets:
        GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=GEMINI_KEY)
    else:
        st.warning("Advertencia: No se encontraron secretos. La función de IA no funcionará sin la clave 'GEMINI_API_KEY'.")
except KeyError:
    st.error("Error de Configuración: La clave 'GEMINI_API_KEY' no se encuentra en el archivo .streamlit/secrets.toml.")
except Exception as e:
    st.error(f"Error al inicializar la API de Gemini: {e}")


# --- FUNCIONES DE LA IA ---

def generate_seo_suggestions(title, meta_desc, content_text):
    """Llama a la API de Gemini para obtener sugerencias de Título y Meta Description."""
    if not client:
        return "IA no disponible (Error en la clave de API)."

    # Definimos el prompt de Ingeniería (Instrucción a la IA)
    prompt = f"""
    Eres un experto en SEO con 10 años de experiencia. Tu tarea es analizar los siguientes metadatos y contenido de una página web y proponer optimizaciones que mejoren el Click-Through Rate (CTR) en los resultados de búsqueda.

    --- Datos de la página ---
    Título actual: {title}
    Meta Description actual: {meta_desc}
    Contenido principal (Fragmento): {content_text[:1200]} 

    --- Tarea ---
    1. Propón 1 Título SEO mejorado (menos de 60 caracteres) con un foco claro en palabras clave y CTR.
    2. Propón 1 Meta Description optimizada (menos de 150 caracteres) que sea un llamado a la acción persuasivo y que use palabras clave del texto.

    Formatea tu respuesta de la siguiente manera:
    TÍTULO PROPUESTO: [Tu nuevo título]
    META DESCRIPTION PROPUESTA: [Tu nueva descripción]
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Modelo rápido y eficiente para texto
            contents=prompt,
        )
        # Aseguramos que solo devolvemos el texto generado
        return response.text.strip()
    except Exception as e:
        # En caso de error de conexión o cuota, devolvemos el error.
        return f"Error en la API de Gemini: {e}"

# --- FUNCIONES DEL CRAWLER ---

def check_robots_txt(base_url):
    """Verifica la existencia y el estado de robots.txt."""
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = requests.get(robots_url, timeout=5)
        if response.status_code == 200:
            return True, "Encontrado (200 OK)"
        else:
            return False, f"No encontrado o error ({response.status_code})"
    except:
        return False, "Error de conexión"

def analyze_page(url):
    """Extrae datos SEO clave y llama a la función de IA."""
    try:
        headers = {'User-Agent': 'SEO-Audit-Bot/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        status_code = response.status_code

        if status_code != 200:
             return {"URL": url, "Status": status_code, "Title": "N/A", "Title Length": 0, "H1": "N/A", "Meta Description": "N/A", "Word Count": 0, "Audit Flags": f"❌ Código de Error {status_code}", "IA Suggestions": "No analizado (Error HTTP)"}

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extracción de datos
        title = soup.title.string.strip() if soup.title else ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_desc_content = meta_desc["content"].strip() if meta_desc else ""
        h1 = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
        
        # Extracción de texto limpio 
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
        text_content = soup.get_text(separator=' ', strip=True)
        word_count = len(text_content.split())
        
        # Auditoría básica
        audit_notes = []
        if not title: audit_notes.append("Falta Title")
        if len(title) > 60: audit_notes.append("Title muy largo")
        if not meta_desc_content: audit_notes.append("Falta Meta Desc")
        if not h1: audit_notes.append("Falta H1")
        if word_count < 300: audit_notes.append("Contenido pobre (<300 palabras)")

        # Llama a la IA para obtener sugerencias (solo si hay suficiente contenido)
        if len(text_content) > 100:
            ia_suggestions = generate_seo_suggestions(title, meta_desc_content, text_content)
        else:
            ia_suggestions = "Contenido muy corto para análisis de IA."

        return {
            "URL": url,
            "Status": status_code,
            "Title": title,
            "Title Length": len(title),
            "H1": h1,
            "Meta Description": meta_desc_content,
            "Word Count": word_count,
            "Audit Flags": ", ".join(audit_notes) if audit_notes else "✅ Óptimo",
            "IA Suggestions": ia_suggestions, # Nuevo campo con las sugerencias
            "Full Text (Fragment)": text_content[:500] + "..." # Fragmento del texto completo
        }
    except Exception as e:
        return {"URL": url, "Status": "Error", "Title": "N/A", "Title Length": 0, "H1": "N/A", "Meta Description": "N/A", "Word Count": 0, "Audit Flags": f"❌ Error de Extracción: {e}", "IA Suggestions": "N/A", "Full Text (Fragment)": "N/A"}

def simple_crawler(start_url, max_pages=10):
    """Función principal del crawler que recorre el sitio."""
    visited = set()
    to_visit = [start_url]
    results = []
    
    domain = urlparse(start_url).netloc
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    count = 0
    
    while to_visit and count < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
            
        status_text.text(f"Analizando página {count + 1}/{max_pages}: {current_url}...")
        data = analyze_page(current_url)
        results.append(data)
        visited.add(current_url)
        
        # Buscar nuevos enlaces internos para seguir
        if data.get("Status") == 200:
            try:
                # Usamos una solicitud separada para la extracción de enlaces para no re-renderizar
                r = requests.get(current_url, timeout=5)
                s = BeautifulSoup(r.content, 'html.parser')
                for a in s.find_all('a', href=True):
                    link = urljoin(start_url, a['href'])
                    
                    # Filtramos enlaces externos y duplicados
                    if urlparse(link).netloc == domain and link not in visited and link not in to_visit and not link.endswith(('.pdf', '.png', '.jpg', '.gif')):
                        to_visit.append(link)
            except:
                pass
        
        count += 1
        progress_bar.progress(count / max_pages)
        time.sleep(0.5) # Pausa de 0.5s para ser amable con el servidor (evitar bloqueos)
        
    status_text.text("¡Análisis completado!")
    return pd.DataFrame(results)

# --- INTERFAZ DE USUARIO ---

url_input = st.text_input("Introduce la URL de la Home (ej: https://ejemplo.com)", "")
max_pages_slider = st.slider("¿Cuántas páginas quieres analizar como máximo?", 5, 100, 20)

if st.button("🚀 Iniciar Auditoría (Crawler + IA)"):
    if not url_input.startswith(('http://', 'https://')):
        st.error("Por favor introduce una URL que empiece con http:// o https://")
    else:
        # 1. Chequeo Robots.txt
        st.subheader("1. Estado de Robots.txt")
        exists, msg = check_robots_txt(url_input)
        if exists:
            st.success(f"Robots.txt: {msg}")
        else:
            st.warning(f"Robots.txt: {msg}")
            
        # 2. Crawler y Auditoría
        st.subheader("2. Extracción, Auditoría y Sugerencias de IA")
        df_results = simple_crawler(url_input, max_pages_slider)
        
        # Reordenar las columnas para poner las sugerencias de la IA al principio
        cols = ["URL", "Status", "Audit Flags", "IA Suggestions", "Title", "H1", "Meta Description", "Word Count", "Full Text (Fragment)"]
        df_results = df_results[cols]

        # Mostrar tabla interactiva (ajustamos el ancho de las columnas)
        st.dataframe(df_results, use_container_width=True, column_config={
            "IA Suggestions": st.column_config.Column(width="large"),
            "Title": st.column_config.Column(width="medium"),
            "Meta Description": st.column_config.Column(width="medium"),
        })
        
        # 3. Descarga
        st.subheader("3. Descargar Datos")
        csv = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Descargar reporte completo en CSV",
            data=csv,
            file_name='seo_audit_report_gemini.csv',
            mime='text/csv',
        )
