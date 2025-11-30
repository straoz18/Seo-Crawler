import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import time
import json 
import base64
import re 
from io import BytesIO 

# Importaciones de la API de Google Gemini (Asegúrate de que 'google-genai' esté en requirements.txt)
from google import genai
from google.genai import types


# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="SEO & pSEO AI Tool", layout="wide")


# --- CONFIGURACIÓN DE AUTENTICACIÓN ---
ADMIN_USER = "admin"
ADMIN_PASS = "Creativos.2025//"

# El nombre completo de la primera página (debe coincidir exactamente con la opción del menú)
DEFAULT_PAGE = "📊 Crawler & Auditoría SEO"

# Inicializar el estado de autenticación
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'current_page' not in st.session_state:
    # CORRECCIÓN: Inicializar con el nombre completo y el emoji
    st.session_state['current_page'] = DEFAULT_PAGE


# --- ESTILOS CSS GENERALES ---
# Nueva paleta de colores:
# Primario (Dark Blue): #1E3A8A
# Secundario (Cyan): #06B6D4 

def apply_custom_css():
    st.markdown("""
        <style>
        /* Ocultar Streamlit Menu y Footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* --- COLORES Y FUENTES --- */
        body { font-family: 'Inter', sans-serif; }
        
        /* Título Principal */
        h1 { 
            color: #1E3A8A; /* Azul Oscuro */
            border-bottom: 2px solid #E5E7EB; 
            padding-bottom: 5px;
            margin-bottom: 20px;
        }
        
        /* Subtítulos */
        h2 { 
            color: #06B6D4; /* Cian */
            margin-top: 25px;
            margin-bottom: 15px;
        }

        /* Botones y Elementos Interactivos */
        .stButton>button, .stDownloadButton>button {
            background-color: #06B6D4 !important; /* Cian */
            color: white !important;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            height: 40px;
            transition: background-color 0.3s;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background-color: #0891B2 !important; /* Cian más oscuro */
        }
        
        /* Contenedores de Alerta (Info, Success, Warning) */
        .stAlert {
            border-left: 5px solid #1E3A8A; /* Barra lateral Azul Oscuro */
            border-radius: 8px;
        }
        
        /* --- SIDEBAR Y NAVEGACIÓN --- */
        /* Estilos generales de la sidebar */
        .st-emotion-cache-1ldf153 {
            background-color: #F8FAFC; /* Fondo muy claro para la sidebar */
        }
        
        /* Título del logo en la sidebar */
        .sidebar-header {
            color: #1E3A8A; /* Azul Oscuro */
            font-weight: 700;
            margin-bottom: 10px;
        }

        /* Contenedor de la barra de navegación */
        .st-emotion-cache-170y540 > div > div:nth-child(2) > div {
             /* El selector para el menu de radio de Streamlit es complejo */
             /* Le daremos un estilo simple de botones grandes */
        }
        
        /* --- LOGIN FORM STYLES (Centrado y Moderno) --- */
        .centered-container {
            display: flex;
            justify-content: center;
            margin-top: 15vh; 
            flex-direction: column;
            align-items: center; 
        }

        .login-card {
            padding: 30px 40px;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
            background: #ffffff !important; 
            color: #333333 !important; 
            width: 100%;
            max-width: 400px; 
            text-align: center;
        }
        
        /* Forzar texto de la tarjeta y etiquetas oscuras */
        .login-card h2, .login-card p, .login-card label p {
            color: #1E3A8A !important; /* Azul Oscuro */
        }
        </style>
    """, unsafe_allow_html=True)

# Función para el logo (SVG con el nuevo color)
def get_svg_logo(color="#06B6D4"):
    # Misma araña, nuevo color cian
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
            {get_svg_logo("#1E3A8A")}
            <h2 style="color: #1E3A8A !important;">Acceso a Herramienta SEO</h2>
            <p style="color: #666; margin-bottom: 20px;">Introduce tus credenciales.</p>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuario", key="user_input")
        password = st.text_input("Clave", type="password", key="pass_input")
        submitted = st.form_submit_button("Acceder")
        
        if submitted:
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state['authenticated'] = True
                st.success("Acceso concedido. Recargando aplicación...")
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


# --- FUNCIONES DE IA Y CRAWLER (SIN CAMBIOS EN LÓGICA) ---

# --- INICIALIZACIÓN Y GESTIÓN DE LA CLAVE DE API ---
client = None
try:
    # Intenta obtener la clave de secrets.toml
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_KEY)
except KeyError:
    # Si la clave no está, avisa que la IA no funcionará
    st.sidebar.error("Error: 'GEMINI_API_KEY' no configurada en `secrets.toml`. Las funciones de IA no están disponibles.")
except Exception as e:
    st.sidebar.error(f"Error al inicializar la API de Gemini: {e}")

# --- FUNCIONES DE LA IA (COMPARTIDAS) ---

def call_gemini_with_json(prompt, schema, use_search=False):
    """Función auxiliar para hacer llamadas a la API de Gemini con respuesta JSON.
    Incluye opción para usar Google Search (grounding)."""
    if not client:
        return None
    
    # Configuración de herramientas (Google Search)
    tools = [{"google_search": {}}] if use_search else None
    
    config_params = {}
    if not use_search:
        config_params['response_mime_type'] = "application/json"
        config_params['response_schema'] = schema

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                **config_params,
                tools=tools
            )
        )
        
        if use_search:
            # Si se usó Google Search, la respuesta es texto plano/markdown
            return response.text.strip()
        else:
            # Si no se usó Google Search, se espera JSON
            return json.loads(response.text.strip())
        
    except Exception as e:
        # En caso de error de la API, imprimir el error y retornar None
        st.error(f"Error al llamar a Gemini: {e}")
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

# --- NUEVA FUNCIÓN PARA ANÁLISIS DE NICHO Y COMPETENCIA (pSEO 3) ---

def analyze_and_suggest_keywords(url):
    """Analiza una URL, su nicho, competidores y sugiere keywords pSEO usando Google Search."""
    
    prompt = f"""
    Eres un analista de SEO Programático especializado en el análisis de nichos de mercado.
    Tu tarea es analizar la siguiente URL: {url}.

    Pasos a seguir (usando la herramienta de Google Search):
    1. Determinar el nicho de mercado, la propuesta de valor y el rubro de la URL.
    2. Identificar al menos 3 competidores clave y analizar qué tipo de contenido están creando.
    3. En base al nicho y las debilidades/oportunidades encontradas en la competencia, generar 10 keywords de cola larga (long-tail) que sean perfectas para una estrategia de SEO Programático para la URL de entrada.

    Estructura de respuesta:
    1. **RESUMEN DE NICHO:** Proporciona un resumen conciso del nicho de mercado y propuesta de valor de la web analizada.
    2. **INSIGHTS COMPETITIVOS:** Breve análisis de las estrategias de palabras clave de los principales competidores encontrados (menciona al menos 3).
    3. **KEYWORDS DE OPORTUNIDAD:** Genera una tabla en formato Markdown con las 10 keywords pSEO sugeridas. La tabla debe tener exactamente 3 columnas: 'Keyword Sugerida', 'Intención de Búsqueda' (Informativa, Transaccional, etc.) y 'Estimación de Dificultad' (Baja, Media, Alta).
    
    Asegúrate de que la tabla Markdown empiece y termine con el formato de tabla estándar de Markdown.
    """
    
    # Retorna un string (texto plano/markdown)
    return call_gemini_with_json(prompt, schema=None, use_search=True)

def parse_markdown_table(markdown_text):
    """Extrae la tabla Markdown del texto y la convierte en DataFrame."""
    
    # 1. Encontrar el bloque de la tabla
    # Busca el patrón de tabla Markdown (líneas separadas por |)
    table_match = re.search(r'\|.*\|.*\n\|---.*\|\n((\|.*\|\n?)+)', markdown_text, re.DOTALL)
    
    if not table_match:
        return None

    table_block = table_match.group(0).strip()
    
    # 2. Procesar las filas
    lines = table_block.split('\n')
    
    # La cabecera es la primera línea (índice 0)
    header = [h.strip() for h in lines[0].strip('|').split('|')]
    
    # Los datos comienzan después de la línea separadora (índice 2 en adelante)
    data_rows = []
    for line in lines[2:]:
        # Ignorar líneas vacías
        if not line.strip():
            continue
        # Limpiar y dividir los valores
        row_values = [v.strip() for v in line.strip('|').split('|')]
        # Asegurarse de que tengamos el número correcto de columnas
        if len(row_values) == len(header):
            data_rows.append(row_values)

    df = pd.DataFrame(data_rows, columns=header)
    return df

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

# --- FUNCIÓN DE GENERACIÓN DE PDF ---

def generate_pdf_report(title, content_list, filename="reporte.pdf"):
    """
    Simula la generación de un PDF a partir de una lista de strings de contenido
    y devuelve los bytes para la descarga.
    """
    
    # Contenido del PDF simulado
    pdf_content = f"REPORTE PDF DE {title.upper()}\n\n"
    pdf_content += "=" * 50 + "\n\n"
    
    for item in content_list:
        pdf_content += item + "\n"
        pdf_content += "-" * 50 + "\n"
        
    # Crear un buffer de bytes para simular el archivo PDF
    buffer = BytesIO()
    buffer.write(pdf_content.encode('utf-8'))
    buffer.seek(0)
    
    return buffer.getvalue()


# --- DEFINICIÓN DE PÁGINAS ---

def render_seo_audit_page():
    """Renderiza la página del Crawler y Auditoría SEO."""
    st.subheader("Herramienta de Auditoría y Extracción Web")
    st.info("Utiliza Gemini para sugerir optimizaciones de Título y Meta Descripción de cada página rastreada.")
    
    url_input = st.text_input("Introduce la URL de la Home (ej: https://ejemplo.com)", key="audit_url_input")
    max_pages_slider = st.slider("¿Cuántas páginas quieres analizar como máximo?", 5, 100, 20, key="audit_pages_slider")

    if st.button("🚀 Iniciar Auditoría (Crawler + IA)", use_container_width=True, key="btn_start_audit"):
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
            
            # Guardar el DataFrame en el estado de sesión para la descarga
            st.session_state['audit_df'] = df_results
            
            # Reordenar las columnas
            cols = ["URL", "Status", "Audit Flags", "IA Suggestions", "Title", "H1", "Meta Description", "Word Count", "Full Text (Fragment)"]
            df_results = df_results[cols]

            # Mostrar tabla interactiva. 
            st.dataframe(df_results, use_container_width=True, column_config={
                "IA Suggestions": st.column_config.Column(width="large"),
                "Title": st.column_config.Column(width="medium"),
                "Meta Description": st.column_config.Column(width="medium"),
            })
            
            # 3. Opciones de Descarga
            st.subheader("3. Opciones de Descarga")
            col_csv, col_pdf = st.columns(2)
            
            with col_csv:
                csv = df_results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Descargar reporte CSV",
                    data=csv,
                    file_name='seo_audit_report_gemini.csv',
                    mime='text/csv',
                    use_container_width=True
                )
            
            with col_pdf:
                # Preparar contenido para el PDF
                pdf_content_list = ["--- Resultados del Crawler ---"]
                for index, row in df_results.iterrows():
                    page_report = f"Página: {row['URL']}\n"
                    page_report += f"Estado HTTP: {row['Status']}\n"
                    page_report += f"Banderas de Auditoría: {row['Audit Flags']}\n"
                    page_report += f"Sugerencias IA:\n{row['IA Suggestions']}"
                    pdf_content_list.append(page_report)

                pdf_data = generate_pdf_report(
                    title=f"Auditoría SEO: {urlparse(url_input).netloc}",
                    content_list=pdf_content_list,
                )
                
                st.download_button(
                    label="📄 Descargar reporte PDF",
                    data=pdf_data,
                    file_name='seo_audit_report_gemini.pdf',
                    mime='application/octet-stream', 
                    use_container_width=True
                )
    
    # Esto es para que si se recarga la página, pero ya hay un DataFrame guardado, se muestre
    if 'audit_df' in st.session_state and not st.session_state['audit_df'].empty:
        st.subheader("Resultados Anteriores del Crawler")
        df_results = st.session_state['audit_df']
        cols = ["URL", "Status", "Audit Flags", "IA Suggestions", "Title", "H1", "Meta Description", "Word Count", "Full Text (Fragment)"]
        df_results = df_results[cols]
        st.dataframe(df_results, use_container_width=True)


def render_pseo_tool_page():
    """Renderiza la nueva página de SEO Programático."""
    st.subheader("Generación de Contenido Programático con IA")
    st.info("Utiliza la IA para generar una base de datos de variaciones de *keywords* y estructuras de contenido para tus páginas de pSEO.")

    # Mantenemos las pestañas internas para la funcionalidad dentro de esta página
    tab1, tab2, tab3 = st.tabs([
        "1. Generar Variaciones Manuales", 
        "2. Generar Estructura de Contenido", 
        "3. Análisis de Nicho & Keywords Competitivas"
    ])

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
                        st.session_state['variations_df'] = df_vars # Guardar en sesión
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
                        st.session_state['template_data'] = template # Guardar en sesión
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

    with tab3:
        st.markdown("### Análisis Competitivo para pSEO")
        st.info("Introduce una URL para que la IA analice su nicho, identifique competidores y sugiera *keywords* de oportunidad.")
        
        target_url = st.text_input("URL de la Web a Analizar (ej: https://suempresa.com)", key="pseo_niche_url")
        
        if st.button("Analizar Nicho y Competencia", key="btn_niche_analysis", use_container_width=True):
            if target_url and client:
                if not target_url.startswith(('http://', 'https://')):
                    st.error("Por favor, introduce una URL que empiece con http:// o https://")
                else:
                    with st.spinner(f"Analizando la URL y la competencia de '{target_url}' usando Google Search..."):
                        # Llamada que devuelve Markdown simple (Grounding permitido)
                        analysis_markdown = analyze_and_suggest_keywords(target_url)
                        
                        if analysis_markdown:
                            st.session_state['niche_analysis_data'] = analysis_markdown # Guardar en sesión
                            
                            # 1. Mostrar texto introductorio y análisis.
                            st.success("¡Análisis Competitivo y Sugerencias de Keywords completado!")

                            # Usamos regex para extraer las secciones de texto antes de la tabla.
                            # Extraemos el resumen de nicho
                            niche_match = re.search(r'\*\*RESUMEN DE NICHO:\*\*(.*?)(?=\*\*INSIGHTS COMPETITIVOS:\*\*|\Z)', analysis_markdown, re.DOTALL)
                            niche_summary = niche_match.group(1).strip() if niche_match else "N/A"
                            if niche_match:
                                st.subheader("1. Resumen de Nicho y Propuesta de Valor")
                                st.markdown(niche_summary)

                            # Extraemos los insights competitivos
                            insights_match = re.search(r'\*\*INSIGHTS COMPETITIVOS:\*\*(.*?)(?=\*\*KEYWORDS DE OPORTUNIDAD:\*\*|\Z)', analysis_markdown, re.DOTALL)
                            competitive_insights = insights_match.group(1).strip() if insights_match else "N/A"
                            if insights_match:
                                st.subheader("2. Insights Clave de la Competencia")
                                st.markdown(competitive_insights)

                            # 2. Keywords Sugeridas (Parseando la tabla)
                            st.subheader("3. 10 Keywords pSEO de Oportunidad")
                            
                            df_keywords = parse_markdown_table(analysis_markdown)
                            st.session_state['keywords_df'] = df_keywords # Guardar en sesión
                            
                            if df_keywords is not None and not df_keywords.empty:
                                st.dataframe(df_keywords, use_container_width=True)

                                # 3. Opciones de Descarga
                                st.subheader("4. Opciones de Descarga")
                                col_csv_kw, col_pdf_niche = st.columns(2)
                                
                                with col_csv_kw:
                                    csv_keywords = df_keywords.to_csv(index=False).encode('utf-8')
                                    st.download_button(
                                        label="💾 Descargar CSV de Keywords",
                                        data=csv_keywords,
                                        file_name='pseo_keywords_competitivas.csv',
                                        mime='text/csv',
                                        use_container_width=True
                                    )
                                
                                with col_pdf_niche:
                                    # Preparar contenido para el PDF de Nicho
                                    pdf_content_list = [
                                        f"URL Analizada: {target_url}",
                                        "\n--- Resumen de Nicho y Propuesta de Valor ---\n",
                                        niche_summary,
                                        "\n--- Insights Clave de la Competencia ---\n",
                                        competitive_insights,
                                        "\n--- Keywords pSEO de Oportunidad ---\n",
                                        df_keywords.to_markdown(index=False) # Agregar tabla como Markdown
                                    ]

                                    pdf_data = generate_pdf_report(
                                        title=f"Análisis de Nicho para: {urlparse(target_url).netloc}",
                                        content_list=pdf_content_list,
                                    )

                                    st.download_button(
                                        label="📄 Descargar reporte PDF",
                                        data=pdf_data,
                                        file_name='pseo_niche_analysis.pdf',
                                        mime='application/octet-stream',
                                        use_container_width=True
                                    )

                            else:
                                st.warning("La IA generó el análisis, pero no se pudo extraer la tabla de keywords. Aquí está la respuesta completa en bruto para revisión:")
                                st.code(analysis_markdown, language="markdown")

                        else:
                            st.warning("No se pudo completar el análisis. Inténtalo con otra URL o verifica la clave de API.")
            elif not client:
                st.error("La API de Gemini no está configurada correctamente.")
            else:
                st.warning("Por favor, introduce una URL para empezar el análisis.")


# --- LÓGICA PRINCIPAL DE LA APLICACIÓN (AUTENTICADA) ---

# TÍTULO Y LOGO EN LA BARRA LATERAL
with st.sidebar:
    st.markdown(f"""
        <div style='text-align: center; padding-top: 10px; padding-bottom: 20px; border-bottom: 1px solid #E5E7EB;'>
            {get_svg_logo("#1E3A8A")}
            <p class='sidebar-header'>SEO AI Suite</p>
            <p style='font-size: 0.8em; color: #777;'>Bienvenido, {ADMIN_USER}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # MENÚ DE NAVEGACIÓN LATERAL
    st.markdown("### Navegación")
    
    # Lista de todas las opciones del menú
    MENU_OPTIONS = [DEFAULT_PAGE, "💡 pSEO - Programmatic SEO"]
    
    page_selection = st.radio(
        "Elige una herramienta",
        MENU_OPTIONS,
        # Usar la lista de opciones para encontrar el índice de la página actual
        index=MENU_OPTIONS.index(st.session_state['current_page']),
        key="main_menu_radio"
    )
    
    # Actualizar el estado de sesión al hacer clic
    st.session_state['current_page'] = page_selection
    
    # Lógica de cierre de sesión al final de la barra lateral
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True) # Espaciador
    if st.button("Cerrar Sesión", key="logout_btn_main", use_container_width=True): 
        st.session_state['authenticated'] = False
        st.rerun()

# CONTENIDO PRINCIPAL BASADO EN LA SELECCIÓN DEL MENÚ
st.title("🤖 SEO AI Suite - Herramientas Programáticas y de Auditoría por Israel Ríos")

if st.session_state['current_page'] == DEFAULT_PAGE:
    render_seo_audit_page()

elif st.session_state['current_page'] == "💡 pSEO - Programmatic SEO":
    render_pseo_tool_page()
