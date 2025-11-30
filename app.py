import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="SEO Audit Tool Pro", layout="wide")

st.title("🕷️ Herramienta de Auditoría y Extracción SEO - Israel")
st.markdown("""
Esta herramienta extraerá el contenido, validará metadatos y revisará el estado técnico básico.
""")

# --- FUNCIONES DEL NÚCLEO ---

def get_status_emoji(code):
    if code == 200: return "✅"
    if code == 404: return "❌"
    if code == 500: return "⚠️"
    return "❓"

def check_robots_txt(base_url):
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
    try:
        headers = {'User-Agent': 'SEO-Audit-Bot/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extracción de datos
        title = soup.title.string if soup.title else ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_desc_content = meta_desc["content"] if meta_desc else ""
        h1 = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
        
        # Extracción de texto limpio (para tu optimización posterior)
        # Eliminamos scripts y estilos para que solo quede texto humano
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
        text_content = soup.get_text(separator=' ')
        word_count = len(text_content.split())
        
        # Auditoría básica
        audit_notes = []
        if not title: audit_notes.append("Falta Title")
        if len(title) > 60: audit_notes.append("Title muy largo")
        if not meta_desc_content: audit_notes.append("Falta Meta Desc")
        if not h1: audit_notes.append("Falta H1")
        if word_count < 300: audit_notes.append("Contenido pobre (Thin Content)")

        return {
            "URL": url,
            "Status": response.status_code,
            "Title": title,
            "Title Length": len(title),
            "H1": h1,
            "Meta Description": meta_desc_content,
            "Word Count": word_count,
            "Audit Flags": ", ".join(audit_notes) if audit_notes else "✅ Óptimo",
            "Full Text": text_content[:500] + "..." # Guardamos solo el inicio para previsualizar
        }
    except Exception as e:
        return {"URL": url, "Status": "Error", "Audit Flags": str(e)}

def simple_crawler(start_url, max_pages=10):
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
            
        status_text.text(f"Analizando: {current_url}...")
        data = analyze_page(current_url)
        results.append(data)
        visited.add(current_url)
        
        # Buscar nuevos enlaces internos para seguir
        if data.get("Status") == 200:
            try:
                r = requests.get(current_url, timeout=5)
                s = BeautifulSoup(r.content, 'html.parser')
                for a in s.find_all('a', href=True):
                    link = urljoin(start_url, a['href'])
                    if urlparse(link).netloc == domain and link not in visited and link not in to_visit:
                        to_visit.append(link)
            except:
                pass
        
        count += 1
        progress_bar.progress(count / max_pages)
        time.sleep(0.5) # Pausa para ser amable con el servidor
        
    status_text.text("¡Análisis completado!")
    return pd.DataFrame(results)

# --- INTERFAZ DE USUARIO ---

url_input = st.text_input("Introduce la URL de la Home (ej: https://ejemplo.com)", "")
max_pages_slider = st.slider("¿Cuántas páginas quieres analizar como máximo?", 5, 100, 20)

if st.button("🚀 Iniciar Auditoría"):
    if not url_input:
        st.error("Por favor introduce una URL válida.")
    else:
        # 1. Chequeo Robots.txt
        st.subheader("1. Estado de Robots.txt")
        exists, msg = check_robots_txt(url_input)
        if exists:
            st.success(f"Robots.txt: {msg}")
        else:
            st.warning(f"Robots.txt: {msg}")
            
        # 2. Crawler y Auditoría
        st.subheader("2. Extracción y Análisis de Páginas")
        df_results = simple_crawler(url_input, max_pages_slider)
        
        # Mostrar tabla interactiva
        st.dataframe(df_results)
        
        # 3. Descarga
        st.subheader("3. Descargar Datos")
        csv = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Descargar reporte en CSV",
            data=csv,
            file_name='seo_audit_report.csv',
            mime='text/csv',
        )
