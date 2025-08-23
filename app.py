import streamlit as st
import google.generativeai as genai
import pandas as pd
import json

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Taller de Datos RAG v2",
    page_icon=" directing_traffic",
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

# --- FUNCIÓN PARA CONVERTIR JSON A MARKDOWN ---
def json_to_markdown(data):
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

# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN ---
if 'structured_text' not in st.session_state:
    st.session_state.structured_text = "El resultado aparecerá aquí."
if 'original_content' not in st.session_state:
    st.session_state.original_content = ""

# --- INTERFAZ DE LA APLICACIÓN ---
st.title(" directing_traffic Taller de Estructuración de Datos Dirigido por IA")
st.markdown("Carga tu documento, dale instrucciones a la IA sobre cómo procesarlo y obtén un resultado estructurado y consistente.")

col1, col2 = st.columns(2, gap="large")

# --- COLUMNA 1: ENTRADA E INSTRUCCIONES ---
with col1:
    st.subheader("1. Carga tu Documento")
    with st.container(border=True, height=300):
        input_method_tab, file_upload_tab = st.tabs(["Pegar Texto", "Subir Archivo Excel"])
        with input_method_tab:
            text_input = st.text_area("Pega texto aquí", height=200)
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
    
    st.subheader("2. Da Instrucciones a la IA (Opcional)")
    with st.container(border=True, height=300):
        instructions = st.text_area(
            "Describe cómo debe procesar el documento.",
            placeholder="Ej: 'Extrae solo los nombres y las fechas clave.' o 'Enfócate en la sección de riesgos y resume cada punto en una frase.'",
            height=200
        )

# --- COLUMNA 2: PROCESAMIENTO Y RESULTADO ---
with col2:
    st.subheader("3. Procesa y Edita el Resultado")
    
    process_button = st.button("Procesar Documento", type="primary", use_container_width=True)

    with st.container(border=True, height=520):
        if process_button:
            if st.session_state.original_content:
                with st.spinner("🤖 La IA está procesando el documento según tus instrucciones..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        generation_config = genai.types.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=SCHEMA
                        )
                        
                        user_instructions = instructions if instructions.strip() else "Procede con el análisis estándar."
                        
                        prompt = f"""
                        Tu tarea es actuar como un analista de datos experto.
                        Primero, lee las 'INSTRUCCIONES DEL USUARIO' para entender el objetivo del análisis.
                        Luego, analiza el 'TEXTO ORIGINAL' siguiendo esas instrucciones.
                        Finalmente, extrae la información resultante y rellena de forma estricta y completa el esquema JSON proporcionado.

                        --- INSTRUCCIONES DEL USUARIO ---
                        {user_instructions}

                        --- TEXTO ORIGINAL ---
                        {st.session_state.original_content}
                        --- FIN DEL TEXTO ---
                        """
                        
                        response = model.generate_content(prompt, generation_config=generation_config)
                        structured_json = json.loads(response.text)
                        st.session_state.structured_text = json_to_markdown(structured_json)
                        st.success("¡Documento procesado!")

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
