import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import time
import json 
import base64

# Importaciones de la API de Google Gemini (Asegúrate de que 'google-genai' esté en requirements.txt)
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="SEO & pSEO AI Tool", layout="wide")


# --- CONFIGURACIÓN DE AUTENTICACIÓN ---
ADMIN_USER = "admin"
ADMIN_PASS = "Creativos.2025//"

# Inicializar el estado de autenticación
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Crawler & Auditoría" # Estado para la navegación superior


# --- ESTILOS CSS GENERALES ---
def apply_custom_css():
    st.markdown("""
        <style>
        /* Estilos Generales */
        body { font-family: 'Inter', sans-serif; }
        
        /* Ocultar Streamlit Menu y Footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Contenedor principal para centrar el login */
        .centered-container {
            display: flex;
            justify-content: center;
            /* Usamos un margen superior fijo para que no se pegue arriba, en lugar de 100vh */
            margin-top: 15vh; 
            flex-direction: column;
            align-items: center; 
        }

        /* Card de Login Estilizada (Forzar colores para Dark Mode) */
        .login-card {
            padding: 30px 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            background: #ffffff !important; /* Fondo blanco forzado */
            color: #333333 !important; /* Texto oscuro forzado */
            width: 100%;
            max-width: 400px; 
            text-align: center;
        }

        /* Forzar texto de la tarjeta y etiquetas oscuras */
        .login-card h2, .login-card p {
            color: #333333 !important; 
        }
        .login-card label p {
            color: #333333 !important; 
        }


        /* Botón de Acceso */
        .stButton>button {
            width: 100%;
            margin-top: 15px;
            background-color: #4CAF50 !important;
            color: white !important;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            height: 40px;
            transition: background-color 0.3s;
        }
        .stButton>button:hover {
            background-color: #45a049 !important;
        }
        
        /* Estilos para las Pestañas (st.tabs) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
            justify-content: center; /* Centrar las pestañas */
        }
        
        /* Pestaña Inactiva */
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: nowrap;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            background-color: #f0f0f0 !important; /* Fondo de pestaña inactiva */
            color: #333333 !important; /* ¡IMPORTANTE! Texto oscuro para asegurar la legibilidad */
            font-size: 1.1em;
            font-weight: 500;
        }
        
        /* Pestaña Activa */
        .stTabs [aria-selected="true"] {
            background-color: #4CAF50 !important; /* Color de pestaña activa */
            color: white !important; /* Texto blanco en pestaña activa */
            border-bottom: 3px solid #4CAF50;
        }

        /* Títulos de la app */
        h1 { color: #4CAF50; }
        h2 { border-bottom: 2px solid #f0f0f0; padding-bottom: 5px; }
        
        /* Dataframes */
        .st-emotion-cache-1mnn93c { border-radius: 8px; }

        </style>
    """, unsafe_allow_html=True)

# Función para el logo (opcional, si quieres usar un SVG o imagen base64)
def get_svg_logo(color="#4CAF50"):
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-spider">
        <path d="M10 9a2 2 0 1 0 4 0 2 2 0 0 0-4 0"/>
        <path d="M12 11v6"/>
        <path d="M8 2v1c0 4.37-3.6 7.9-7.9 7.9"/>
        <path d="M16 2v1c0 4.37 3.6 7.9 7.9 7.9"/>
        <path d="M19.4 14.5c.34-1.11.59-2.29.5-3.5"/>
        <path d="M4.6 14.5c-.34-1.11-.59-2.29-.5-3.5"/>
        <path d="M8.5 22c.39-1.57 2.07-2.92 4-3 1.93-.08 3.61 1.33 4 3"/>
    </svg>
    """
    return svg

def login_form():
    """Muestra el formulario de login centrado."""
    
    apply_custom_css()
    
    st.markdown('<div class="centered-container">', unsafe_allow_html=True)
    
    # Usamos un bloque st.markdown simple para el título y el párrafo dentro de la tarjeta
    st.markdown(f"""
        <div class="login-card">
            {get_svg_logo("#4CAF50")}
            <h2>Acceso a Herramienta SEO</h2>
            <p style="color: #666; margin-bottom: 20px;">Por favor, introduce tus credenciales para continuar.</p>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuario", key="user_input")
        password = st.text_input("Clave", type="password", key="pass_input")
        submitted = st.form_submit_button("Acceder")
        
        if submitted:
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state['authenticated'] = True
                st.success("Acceso concedido. Recargando aplicación...")
                # CORRECCIÓN DE ERROR: Usar st.rerun() que es la función correcta
                st.rerun() 
            else:
                st.error("Usuario o clave incorrecta.")

    # Cierre del div de la tarjeta y del div contenedor centrado
    st.markdown('</div></div>', unsafe_allow_html=True)
    
# Bloquea la aplicación principal si no está autenticado
if not st.session_state['authenticated']:
    login_form()
    st.stop()
    
# Si está autenticado, aplicamos estilos y el código continúa.
apply_custom_css()

# --- INICIALIZACIÓN Y GESTIÓN DE LA CLAVE DE API ---
client = None
try:
    # Intenta obtener la clave de secrets.toml
    # NOTA: La imagen 'image_b1fb9a.png' sugiere un error de NameError aquí si la clave no existe. 
    # Usamos el bloque try/except para manejar correctamente si la clave falta.
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_KEY)
except KeyError:
    # Si la clave no está, avisa que la IA no funcionará
    st.sidebar.error("Error: 'GEMINI_API_KEY' no configurada en `secrets.toml`. Las funciones de IA no están disponibles.")
except Exception as e:
    st.sidebar.error(f"Error al inicializar la API de Gemini: {e}")

# --- FUNCIONES DE LA IA (COMPARTIDAS) ---

def call_gemini_with_json(prompt, schema):
    """Función auxiliar para hacer llamadas a la API de Gemini con respuesta JSON."""
    if not client:
        return None
    try:
        # --- CORRECCIÓN CRÍTICA ---
        # 1. Usar el modelo correcto para generación estructurada: 'gemini-2.5-flash'
        # 2. Descomentar el código de la API real
        # 3. Eliminar los placeholders de prueba
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            )
        )
        # La respuesta de la API ya viene como una cadena JSON, la parseamos.
        return json.loads(response.text.strip())
        
    except Exception as e:
        st.error(f"Error al llamar a Gemini. Verifica tu clave de API y el prompt: {e}")
        return None

# --- FUNCIONES DE IA ESPECÍFICAS DE CRAWLER ---

def generate_seo_suggestions(title, meta_desc, content_text):
    """Llama a la API de Gemini para obtener sugerencias de Título y Meta Description en formato JSON."""
    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "title_propuesto": types.Schema(type=types.Type.STRING, description="El nuevo título SEO mejorado (máx. 60 caracteres)."),
            "meta_description_propuesta": types.Schema(type=types.Type.STRING, description="La nueva Meta Description optimizada (máx. 150 caracteres)."),
        }
    )
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
    
    ia_suggestions_dict = call_gemini_with_json(prompt, schema)
    if ia_suggestions_dict:
        # Formatear el diccionario a una cadena Markdown limpia para el DataFrame
        return f"""
**TÍTULO:** {ia_suggestions_dict.get('title_propuesto', 'N/A')}
**META DESC.:** {ia_suggestions_dict.get('meta_description_propuesta', 'N/A')}
"""
    return "IA no disponible o error de procesamiento."


# --- FUNCIONES DE IA ESPECÍFICAS DE PSEO ---

def generate_pseo_keywords(primary_keyword, num_variations):
    """Genera variaciones de long-tail keywords en formato JSON."""
    schema = types.Schema(
        type=types.Type.ARRAY,
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "variation": types.Schema(type=types.Type.STRING, description="La variación de long-tail keyword o título pSEO."),
                "url_slug": types.Schema(type=types.Type.STRING, description="El slug recomendado para la URL (ej. sin acentos, minúsculas, guiones).")
            }
        )
    )
    prompt = f"""
    Eres un experto en SEO Programático. Genera {num_variations} variaciones de long-tail keywords o títulos de contenido que se puedan usar para crear una base de datos de pSEO basados en el siguiente keyword principal: '{primary_keyword}'.
    Las variaciones deben ser específicas y apuntar a nichos de mercado.
    Ejemplo de Keyword Principal: 'mejores audífonos'
    Ejemplo de Variaciones: 'mejores audífonos para programadores', 'mejores audífonos inalámbricos baratos 2024'.
    DEBES responder estrictamente en formato JSON que se ajuste al esquema proporcionado.
    """
    return call_gemini_with_json(prompt, schema)


def generate_content_template(topic):
    """Genera una estructura de contenido (título, meta, outline) en formato JSON."""
    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "title": types.Schema(type=types.Type.STRING, description="Título SEO final para el artículo (máx. 60 caracteres)."),
            "meta_description": types.Schema(type=types.Type.STRING, description="Meta descripción final para el artículo (máx. 150 caracteres)."),
            "outline": types.Schema(type=types.Type.STRING, description="Estructura detallada del cuerpo del artículo usando encabezados H2 y H3 en formato Markdown.")
        }
    )
    prompt = f"""
    Crea una estructura de contenido detallada para un artículo de SEO Programático basado en el tema: '{topic}'.
    La respuesta debe incluir:
    1. Un Título SEO persuasivo.
    2. Una Meta Descripción optimizada.
    3. Un Outline detallado para el cuerpo del artículo, utilizando Markdown con encabezados H2 y H3 para la jerarquía de contenido.
    DEBES responder estrictamente en formato JSON que se ajuste al esquema proporcionado.
    """
    return call_gemini_with_json(prompt, schema)


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
            formatted_suggestions = generate_seo_suggestions(title, meta_desc_content, text_content)
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
            "IA Suggestions": formatted_suggestions, 
            "Full Text (Fragment)": text_content[:500] + "..."
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

# --- DEFINICIÓN DE PÁGINAS ---

def render_seo_audit_page():
    """Renderiza la página del Crawler y Auditoría SEO (funcionalidad existente)."""
    st.subheader("Herramienta de Auditoría y Extracción Web")
    st.info("Utiliza Gemini para sugerir optimizaciones de Título y Meta Descripción de cada página rastreada.")
    
    url_input = st.text_input("Introduce la URL de la Home (ej: https://ejemplo.com)", "")
    max_pages_slider = st.slider("¿Cuántas páginas quieres analizar como máximo?", 5, 100, 20)

    if st.button("🚀 Iniciar Auditoría (Crawler + IA)", use_container_width=True):
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
            
            # Reordenar las columnas
            cols = ["URL", "Status", "Audit Flags", "IA Suggestions", "Title", "H1", "Meta Description", "Word Count", "Full Text (Fragment)"]
            df_results = df_results[cols]

            # Mostrar tabla interactiva. 
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
                use_container_width=True
            )

def render_pseo_tool_page():
    """Renderiza la nueva página de SEO Programático."""
    st.subheader("Generación de Contenido Programático con IA")
    st.info("Utiliza la IA para generar una base de datos de variaciones de *keywords* y estructuras de contenido para tus páginas de pSEO.")

    tab1, tab2 = st.tabs(["1. Generar Variaciones de Keywords", "2. Generar Estructura de Contenido"])

    with tab1:
        st.markdown("### Generador de Temas Programáticos")
        primary_keyword = st.text_input("Keyword Principal (Ej: Cursos de programación, Mejores teclados)", key="pseo_kw")
        num_variations = st.slider("Número de variaciones a generar", 3, 30, 10, key="pseo_num")
        
        if st.button("Generar Variaciones y Slugs", key="btn_kw_gen", use_container_width=True):
            if primary_keyword and client:
                with st.spinner(f"Generando {num_variations} variaciones para '{primary_keyword}'..."):
                    variations_list = generate_pseo_keywords(primary_keyword, num_variations)
                    
                    if variations_list:
                        df_vars = pd.DataFrame(variations_list)
                        st.success("¡Variaciones generadas con éxito! Usa esta data para tu hoja de cálculo pSEO.")
                        st.dataframe(df_vars, use_container_width=True)
                        
                        # Opción de descarga
                        csv_vars = df_vars.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="💾 Descargar CSV de Variaciones",
                            data=csv_vars,
                            file_name='pseo_variaciones.csv',
                            mime='text/csv',
                            use_container_width=True
                        )
                    else:
                        st.warning("No se pudieron generar variaciones. Verifica la clave de API.")
            elif not client:
                st.error("La API de Gemini no está configurada correctamente.")
            else:
                st.warning("Por favor, introduce un Keyword Principal.")

    with tab2:
        st.markdown("### Generador de Estructura de Contenido (Outline)")
        topic_input = st.text_input("Tema específico para la plantilla (Ej: El mejor software de contabilidad para PYMES)", key="pseo_template_topic")
        
        if st.button("Generar Template de Contenido", key="btn_template_gen", use_container_width=True):
            if topic_input and client:
                with st.spinner(f"Creando la estructura de contenido para '{topic_input}'..."):
                    template = generate_content_template(topic_input)
                    
                    if template:
                        st.success("¡Estructura de contenido generada! Utiliza este *outline* como plantilla para tus páginas programáticas.")
                        
                        col_title, col_meta = st.columns(2)
                        
                        with col_title:
                            st.markdown("**1. Título SEO Propuesto:** (Máx. 60 caracteres)")
                            st.code(template.get('title', 'N/A'))
                        
                        with col_meta:
                            st.markdown("**2. Meta Descripción Propuesta:** (Máx. 150 caracteres)")
                            st.code(template.get('meta_description', 'N/A'))
                        
                        st.markdown("**3. Outline (Estructura en Markdown):**")
                        st.markdown("Copia y pega este código Markdown en tu editor.")
                        st.code(template.get('outline', 'N/A'), language="markdown", height=400)
                        
                        st.markdown("---")
                        st.markdown("### Previsualización de la Estructura")
                        st.markdown(template.get('outline', 'N/A'))
                        
                    else:
                        st.warning("No se pudo generar la estructura. Verifica la clave de API.")
            elif not client:
                st.error("La API de Gemini no está configurada correctamente.")
            else:
                st.warning("Por favor, introduce un tema específico.")

# --- LÓGICA PRINCIPAL DE LA APLICACIÓN (AUTENTICADA) ---

st.sidebar.markdown(f"""
    <div style='text-align: center; padding-top: 10px; padding-bottom: 20px;'>
        {get_svg_logo("#4CAF50")}
        <h3 style='margin-top: 5px; color: #4CAF50;'>SEO AI Suite</h3>
        <p style='font-size: 0.8em; color: #777;'>Bienvenido, {ADMIN_USER}</p>
    </div>
    <div style='text-align: center;'>
        <!-- Nota: Este formulario es más robusto para el logout, pero el botón de Streamlit es más simple y lo usaremos. -->
    </div>
""", unsafe_allow_html=True)

# Lógica de cierre de sesión
# Usamos el botón de Streamlit y forzamos el st.rerun()
if st.sidebar.button("Cerrar Sesión", key="logout_btn_main", use_container_width=True): 
    st.session_state['authenticated'] = False
    st.rerun()

# CONTENIDO PRINCIPAL CON TABS
st.title("🤖 SEO AI Suite - Herramientas Programáticas y de Auditoría")

# Usar st.tabs para la navegación superior (como solicitaste)
tab_audit, tab_pseo = st.tabs(["📊 Crawler & Auditoría SEO", "💡 pSEO - Programmatic SEO"])

with tab_audit:
    render_seo_audit_page()

with tab_pseo:
    render_pseo_tool_page()
