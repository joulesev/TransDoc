import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
from openpyxl import load_workbook

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

# --- NUEVA FUNCIÓN DE PROCESAMIENTO INTELIGENTE ---
def process_excel_file(uploaded_file):
    """
    Lee un archivo Excel, detecta las celdas combinadas, las rellena de forma inteligente
    y devuelve el contenido completo como texto Markdown.
    """
    # Carga el libro de trabajo con openpyxl para leer la estructura
    wb = load_workbook(uploaded_file, read_only=True)
    xls = pd.ExcelFile(uploaded_file)
    
    full_excel_text = []

    for sheet_name in xls.sheet_names:
        ws = wb[sheet_name]
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None) # Leer sin cabecera para alinear índices

        # Obtiene el mapa de celdas combinadas
        merged_ranges = ws.merged_cells.ranges

        # Aplica el relleno inteligente
        for merged_range in merged_ranges:
            # Obtiene los límites del rango (min_col, min_row, max_col, max_row)
            # Los índices de openpyxl empiezan en 1, los de pandas en 0
            min_col, min_row, max_col, max_row = merged_range.bounds
            top_left_cell_value = df.iloc[min_row - 1, min_col - 1]
            
            # Rellena el rango en el DataFrame
            df.iloc[min_row - 1:max_row, min_col - 1:max_col] = top_left_cell_value
        
        # Asigna la primera fila como cabecera y elimina la fila original
        df.columns = df.iloc[0]
        df = df[1:]
        df.reset_index(drop=True, inplace=True)

        if not df.empty:
            full_excel_text.append(f"## Hoja: {sheet_name}\n\n{df.to_markdown(index=False)}\n\n")
            
    return "".join(full_excel_text)


# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN ---
if 'original_content' not in st.session_state:
    st.session_state.original_content = ""
if 'structured_text' not in st.session_state:
    st.session_state.structured_text = "El resultado estructurado por la IA aparecerá aquí..."
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- INTERFAZ DE LA APLICACIÓN ---
st.title("🛠️ Taller de Estructuración de Datos para IA (RAG)")
st.markdown("Sube o pega tu contenido, visualízalo, edítalo y usa un asistente de IA para refinarlo. Finalmente, descarga tu documento en formato Markdown.")

col1, col2, col3 = st.columns([1, 1, 1])

# --- COLUMNA 1: ENTRADA Y VISUALIZACIÓN ---
with col1:
    with st.container(border=True):
        st.subheader("1. Carga y Visualiza")
        
        input_method_tab, file_upload_tab = st.tabs(["Pegar Texto", "Subir Archivo Excel"])

        with input_method_tab:
            text_input = st.text_area("Pega texto sin formato aquí", height=150)
            if text_input:
                st.session_state.original_content = text_input

        with file_upload_tab:
            uploaded_file = st.file_uploader("Sube un archivo .xlsx", type=['xlsx'])
            if uploaded_file:
                try:
                    # Visualización simple
                    xls_preview = pd.ExcelFile(uploaded_file)
                    sheet_to_display = st.selectbox("Selecciona una hoja para visualizar", xls_preview.sheet_names)
                    if sheet_to_display:
                        df_preview = pd.read_excel(xls_preview, sheet_name=sheet_to_display)
                        st.dataframe(df_preview)
                    
                    # Procesa el archivo para la IA en segundo plano
                    st.session_state.original_content = process_excel_file(uploaded_file)
                except Exception as e:
                    st.error(f"Error al leer el archivo: {e}")

        if st.button("Procesar y Estructurar", use_container_width=True, type="primary"):
            if st.session_state.original_content:
                with st.spinner("🤖 Estructurando el documento inicial..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        prompt = f"""
                        Analiza el siguiente texto y reestructúralo en formato Markdown. 
                        Crea un título, un resumen y secciones lógicas. Resalta los datos clave en negrita.

                        --- TEXTO ORIGINAL ---
                        {st.session_state.original_content}
                        --- FIN DEL TEXTO ---
                        """
                        response = model.generate_content(prompt)
                        st.session_state.structured_text = response.text
                        st.success("¡Documento estructurado!")
                    except Exception as e:
                        st.error(f"Error en la estructuración inicial: {e}")
            else:
                st.warning("Por favor, pega texto o sube un archivo.")

# --- COLUMNA 2: EDITOR DE MARKDOWN ---
with col2:
    with st.container(border=True):
        st.subheader("2. Edita el Resultado")
        
        edited_text = st.text_area(
            "Puedes editar el texto directamente aquí",
            value=st.session_state.structured_text,
            height=500,
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

# --- COLUMNA 3: ASISTENTE DE IA ---
with col3:
    with st.container(border=True):
        st.subheader("3. Asistente de Edición")
        
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if instruction := st.chat_input("Da una instrucción para editar..."):
            st.session_state.chat_history.append({"role": "user", "content": instruction})
            with st.chat_message("user"):
                st.markdown(instruction)

            with st.spinner("✍️ La IA está editando el documento..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash-latest')
                    prompt = f"""
                    Actúa como un editor de documentos. Tu tarea es modificar el 'DOCUMENTO ACTUAL' basándote en la 'INSTRUCCIÓN DEL USUARIO'.
                    Debes devolver el **documento completo y modificado**, no solo una respuesta a la instrucción.

                    --- DOCUMENTO ACTUAL ---
                    {st.session_state.structured_text}
                    --- FIN DEL DOCUMENTO ---

                    --- INSTRUCCIÓN DEL USUARIO ---
                    {instruction}
                    --- FIN DE LA INSTRUCCIÓN ---
                    """
                    response = model.generate_content(prompt)
                    
                    st.session_state.structured_text = response.text
                    st.session_state.chat_history = []
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al editar con la IA: {e}")
