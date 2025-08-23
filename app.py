import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Taller de Datos RAG v3",
    page_icon="🛠️",
    layout="wide"
)

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (KeyError, FileNotFoundError):
    st.error("🚨 ¡Error de configuración! No se encontró la clave de API de Gemini.")
    st.warning("Por favor, configura el 'Secreto' de Streamlit llamado `GEMINI_API_KEY`.")
    st.stop()

# --- DEFINICIÓN DEL ESQUEMA JSON ---
# Este es el "formulario" que la IA debe rellenar.
SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "summary": {"type": "STRING"},
        "sections": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "heading": {"type": "STRING"},
                    "content": {"type": "STRING"}
                },
                "required": ["heading", "content"]
            }
        },
        "key_data_points": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "label": {"type": "STRING"},
                    "value": {"type": "STRING"}
                },
                "required": ["label", "value"]
            }
        }
    },
    "required": ["title", "summary", "sections", "key_data_points"]
}

# --- FUNCIONES AUXILIARES ---

def json_to_markdown(data):
    """Convierte el objeto JSON estructurado en un string de Markdown legible."""
    md_parts = []
    md_parts.append(f"# {data.get('title', 'Sin Título')}\n")
    md_parts.append(f"**Resumen:** {data.get('summary', 'No disponible.')}\n")
    if data.get('key_data_points'):
        md_parts.append("## Datos Clave\n")
        for point in data['key_data_points']:
            md_parts.append(f"- **{point.get('label', '')}:** {point.get('value', '')}")
        md_parts.append("\n")
    if data.get('sections'):
        for section in data['sections']:
            md_parts.append(f"## {section.get('heading', 'Sección sin Título')}\n")
            md_parts.append(f"{section.get('content', '')}\n")
    return "\n".join(md_parts)

def extract_json_from_markdown(md_string):
    """Extrae un bloque de código JSON de un string de Markdown."""
    match = re.search(r"```json\n(.*)\n```", md_string, re.DOTALL)
    if match:
        return match.group(1)
    # Intenta encontrar el JSON incluso si no está en un bloque de código
    if md_string.strip().startswith('{'):
        return md_string
    return None

# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN ---
if 'structured_text' not in st.session_state:
    st.session_state.structured_text = "El resultado aparecerá aquí."
if 'original_content' not in st.session_state:
    st.session_state.original_content = ""

# --- INTERFAZ DE LA APLICACIÓN ---
st.title("🛠️ Taller de Estructuración de Datos Dirigido por IA")
st.markdown("Carga tu documento, dale instrucciones a la IA y obtén un resultado estructurado y consistente.")

col1, col2 = st.columns(2, gap="large")

# --- COLUMNA 1: ENTRADA E INSTRUCCIONES ---
with col1:
    st.subheader("1. Carga tu Documento")
    input_method_tab, file_upload_tab = st.tabs(["Pegar Texto", "Subir Archivo Excel"])
    with input_method_tab:
        text_input = st.text_area("Pega texto aquí", height=150, key="text_input_area")
        if text_input:
            st.session_state.original_content = text_input
    with file_upload_tab:
        uploaded_file = st.file_uploader("Sube un archivo .xlsx", type=['xlsx'])
        if uploaded_file:
            try:
                xls = pd.ExcelFile(uploaded_file)
                parts = [f"## Hoja: {name}\n\n{pd.read_excel(xls, name).to_markdown(index=False)}\n" for name in xls.sheet_names]
                st.session_state.original_content = "".join(parts)
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")

    st.subheader("Vista Previa del Contenido Original")
    with st.container(border=True, height=200):
        st.markdown(f"<div style='height:180px;overflow-y:scroll;'>{st.session_state.original_content}</div>", unsafe_allow_html=True)

    st.subheader("2. Da Instrucciones a la IA (Opcional)")
    instructions = st.text_area(
        "Describe cómo debe procesar el documento.",
        placeholder="Ej: 'Extrae solo los nombres y las fechas clave.'",
        height=150
    )

# --- COLUMNA 2: PROCESAMIENTO Y RESULTADO ---
with col2:
    st.subheader("3. Procesa y Edita el Resultado")
    
    process_button = st.button("Procesar Documento", type="primary", use_container_width=True)

    with st.container(border=True, height=520):
        if process_button:
            if st.session_state.original_content:
                with st.spinner("🤖 La IA está procesando el documento..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        
                        user_instructions = instructions if instructions.strip() else "Procede con el análisis estándar."
                        
                        prompt = f"""
                        Tu tarea es actuar como un analista de datos.
                        Lee las 'INSTRUCCIONES DEL USUARIO' y el 'TEXTO ORIGINAL'.
                        Extrae la información solicitada y devuélvela como un objeto JSON que siga estrictamente el esquema proporcionado.
                        Envuelve el objeto JSON final en un bloque de código Markdown ```json ... ```.

                        ESQUEMA JSON:
                        {json.dumps(SCHEMA, indent=2)}

                        INSTRUCCIONES DEL USUARIO:
                        {user_instructions}

                        TEXTO ORIGINAL:
                        {st.session_state.original_content}
                        """
                        
                        response = model.generate_content(prompt)
                        json_string = extract_json_from_markdown(response.text)
                        
                        if json_string:
                            structured_json = json.loads(json_string)
                            st.session_state.structured_text = json_to_markdown(structured_json)
                            st.success("¡Documento procesado!")
                        else:
                            st.error("La IA no devolvió un JSON válido. Su respuesta fue:")
                            st.write(response.text)

                    except Exception as e:
                        st.error(f"Ocurrió un error: {e}")
                        st.session_state.structured_text = "Error al procesar. Intenta con un texto o instrucción más clara."
            else:
                st.warning("Por favor, carga un documento primero.")

        edited_text = st.text_area(
            "Resultado en Markdown (puedes editarlo)",
            value=st.session_state.structured_text,
            height=420
        )
        
        st.download_button(
            label="📥 Descargar Archivo .md",
            data=edited_text,
            file_name="documento_estructurado.md",
            mime="text/markdown",
            use_container_width=True
        )
