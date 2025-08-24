import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import json
import re

# --- CONFIGURACIÓN DE PANDAS ---
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Taller de Datos RAG",
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

# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN ---
if 'structured_text' not in st.session_state:
    st.session_state.structured_text = "El resultado estructurado por la IA aparecerá aquí..."

# --- INTERFAZ DE LA APLICACIÓN ---
st.title("🛠️ Taller de Estructuración de Datos para IA (RAG)")
st.markdown("Sube un archivo de Excel, selecciona una hoja y la IA la limpiará y analizará en dos pasos para garantizar un resultado completo y preciso.")

col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("1. Carga y Procesa por Hoja")
        
        uploaded_file = st.file_uploader("Sube un archivo .xlsx", type=['xlsx'])
        if uploaded_file:
            try:
                xls = pd.ExcelFile(uploaded_file)
                sheet_to_process = st.selectbox("Selecciona una hoja para visualizar y procesar", xls.sheet_names)
                
                if sheet_to_process:
                    df = pd.read_excel(xls, sheet_name=sheet_to_process)
                    st.dataframe(df, height=350)
                    
                    if st.button(f"Procesar Hoja '{sheet_to_process}'", use_container_width=True, type="primary"):
                        # --- INICIO DEL PROCESO DE DOS PASOS ---
                        
                        # PASO 1: LIMPIEZA DE DATOS POR IA
                        with st.spinner("Paso 1/2: La IA está limpiando los datos (celdas combinadas)..."):
                            try:
                                # Convierte la hoja a JSON, preservando los nulos
                                sheet_json_raw = df.to_json(orient='records', indent=2)
                                model_cleaner = genai.GenerativeModel('gemini-1.5-flash-latest')
                                
                                prompt_cleaner = f"""
                                Tu única tarea es limpiar los siguientes datos JSON. Los datos provienen de un Excel con celdas combinadas, lo que genera valores `null`.
                                Debes rellenar cada valor `null` con el último valor no nulo que apareció en la misma columna en una fila anterior.
                                Devuelve **únicamente el objeto JSON completo y limpio**, envuelto en un bloque de código ```json ... ```. No añadas ninguna explicación.

                                --- DATOS JSON CRUDOS ---
                                {sheet_json_raw}
                                --- FIN DE LOS DATOS ---
                                """
                                
                                response_cleaner = model_cleaner.generate_content(prompt_cleaner)
                                
                                # Extraer el JSON limpio de la respuesta
                                clean_json_match = re.search(r"```json\n(.*)\n```", response_cleaner.text, re.DOTALL)
                                if not clean_json_match:
                                    raise ValueError("La IA no devolvió un JSON limpio válido en el Paso 1.")
                                
                                clean_json_str = clean_json_match.group(1)
                                clean_data = json.loads(clean_json_str)
                                st.success("Paso 1/2: Datos limpiados con éxito.")

                            except Exception as e:
                                st.error(f"Error en el Paso 1 (Limpieza): {e}")
                                st.stop()

                        # PASO 2: ANÁLISIS Y ESTRUCTURACIÓN
                        with st.spinner("Paso 2/2: La IA está analizando los datos limpios..."):
                            try:
                                model_analyst = genai.GenerativeModel('gemini-1.5-flash-latest')
                                prompt_analyst = f"""
                                Tu tarea es actuar como un experto analista de datos.
                                A continuación se presenta un conjunto de datos JSON perfectamente limpios. Analízalos en su totalidad.

                                Genera un documento en formato Markdown que sea un resumen detallado y bien estructurado de esos datos.
                                - Crea un título descriptivo.
                                - Escribe un resumen ejecutivo conciso.
                                - Crea secciones lógicas si es apropiado.
                                - Resalta los datos más importantes en negrita.
                                - **Es crucial que no omitas ninguna fila o dato en tu análisis final.**

                                --- DATOS JSON LIMPIOS ---
                                {json.dumps(clean_data, indent=2)}
                                --- FIN DE LOS DATOS ---
                                """
                                response_analyst = model_analyst.generate_content(prompt_analyst)
                                st.session_state.structured_text = response_analyst.text
                                st.success("Paso 2/2: ¡Análisis completado!")
                            
                            except Exception as e:
                                st.error(f"Error en el Paso 2 (Análisis): {e}")
                                st.stop()

            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")

with col2:
    with st.container(border=True):
        st.subheader("2. Edita y Descarga el Resultado")
        edited_text = st.text_area(
            "Puedes editar el texto directamente aquí",
            value=st.session_state.structured_text,
            height=450,
            key="editor"
        )
        st.session_state.structured_text = edited_text
        
        st.download_button(
            label="📥 Descargar Archivo .md",
            data=st.session_state.structured_text,
            file_name="documento_estructurado.md",
            mime="text/markdown",
            use_container_width=True
        )
