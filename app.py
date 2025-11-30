import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import time
import json # Necesario para manejar la respuesta JSON de Gemini

# Importaciones de la API de Google Gemini (Asegúrate de que 'google-genai' esté en requirements.txt)
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="SEO Audit Tool con IA", layout="wide")


# --- CONFIGURACIÓN DE AUTENTICACIÓN ---
ADMIN_USER = "admin"
ADMIN_PASS = "Creativos.2025//"

# Inicializar el estado de autenticación
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def login_form():
    """Muestra el formulario de login en la barra lateral."""
    st.sidebar.title("Login de Acceso")
    with st.sidebar.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Clave", type="password")
        submitted = st.form_submit_button("Acceder")
        
        if submitted:
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state['authenticated'] = True
                st.success("Acceso concedido. Recarga la página para continuar.")
                st.experimental_rerun() # Para recargar la aplicación inmediatamente
            else:
                st.error("Usuario o clave incorrecta.")

# Bloquea la aplicación principal si no está autenticado
if not st.session_state['authenticated']:
    login_form()
    st.stop()
    
# Si está autenticado, el código continúa aquí.
# Botón de cerrar sesión en la barra lateral
if st.sidebar.button("Cerrar Sesión"):
    st.session_state['authenticated'] = False
    st.experimental_rerun()

# --- APP PRINCIPAL (SOLO PARA USUARIOS AUTENTICADOS) ---

st.title("🕷️ Herramienta de Auditoría y Extracción SEO (Impulsada por IA)")
st.markdown("""
Introduce la URL base y el número máximo de páginas. La IA de Gemini sugerirá optimizaciones de Título y Meta Descripción.
""")

# --- INICIALIZACIÓN Y GESTIÓN DE LA CLAVE DE API ---
client = None
try:
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
    """Llama a la API de Gemini para obtener sugerencias de Título y Meta Description en formato JSON."""
    if not client:
        # Devuelve un diccionario vacío o de error para mantener la consistencia del tipo de retorno
        return {"title_propuesto": "IA no disponible", "meta_description_propuesta": "Error en la clave de API."}

    prompt = f"""
    Eres un experto en SEO con 10 años de experiencia. Tu tarea es analizar los siguientes metadatos y contenido de una página web y proponer optimizaciones que mejoren el Click-Through Rate (CTR) en los resultados de búsqueda.

    --- Datos de la página ---
    Título actual: {title}
    Meta Description actual: {meta_desc}
    Contenido principal (Fragmento): {content_text[:1200]} 

    --- Tarea ---
    1. Propón 1 Título SEO mejorado (menos de 60 caracteres).
    2. Propón 1 Meta Description optimizada (menos de 150 caracteres).

    DEBES responder estrictamente en formato JSON que se ajuste al esquema proporcionado. No incluyas ningún texto explicativo fuera del JSON.
    """
    
    # Define el esquema JSON esperado para forzar la estructura
    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "title_propuesto": types.Schema(type=types.Type.STRING, description="El nuevo título SEO mejorado (máx. 60 caracteres)."),
            "meta_description_propuesta": types.Schema(type=types.Type.STRING, description="La nueva Meta Description optimizada (máx. 150 caracteres)."),
        }
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            )
        )
        
        # El texto de respuesta es una cadena JSON que debemos cargar
        return json.loads(response.text.strip())
        
    except Exception as e:
        # Devuelve un diccionario de error en caso de fallo de la API
        return {"title_propuesto": "Error de procesamiento.", "meta_description_propuesta": f"Error: {e}"}

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
             return {"URL": url, "Status": status_code, "Title": "N/A", "Title Length": 0, "H1": "N/A", "Meta Description": "N/A", "Word Count": 0, "Audit Flags": f"❌ Código de Error {status_code}", "IA Suggestions": "No analizado (Error HTTP)", "Full Text (Fragment)": "N/A"}

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
            ia_suggestions_dict = generate_seo_suggestions(title, meta_desc_content, text_content)
            
            # Formatear el diccionario a una cadena Markdown limpia para el DataFrame
            formatted_suggestions = f"""
**TÍTULO:** {ia_suggestions_dict.get('title_propuesto', 'N/A')}
**META DESC.:** {ia_suggestions_dict.get('meta_description_propuesta', 'N/A')}
"""
        else:
            formatted_suggestions = "Contenido muy corto para análisis de IA."

        return {
            "URL": url,
            "Status": status_code,
            "Title": title,
            "Title Length": len(title),
            "H1": h1,
            "Meta Description": meta_desc_content,
            "Word Count": word_count,
            "Audit Flags": ", ".join(audit_notes) if audit_notes else "✅ Óptimo",
            "IA Suggestions": formatted_suggestions, # Usamos la cadena formateada
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

        # Mostrar tabla interactiva. Streamlit soporta saltos de línea y negritas en las celdas del DataFrame
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
