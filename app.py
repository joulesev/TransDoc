import streamlit as st
import google.generativeai as genai
import pandas as pd
import io

# --- CONFIGURACIÓN DE PANDAS ---
# Le damos la orden a pandas de que nunca oculte filas NI TRUNQUE EL TEXTO en las columnas.
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
if 'original_content' not in st.session_state:
    st.session_state.original_content = ""
if 'structured_text' not in st.session_state:
    st.session_state.structured_text = "El resultado estructurado por la IA aparecerá aquí..."
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- INTERFAZ DE LA APLICACIÓN ---
st.title("🛠️ Taller de Estructuración de Datos para IA (RAG)")
st.markdown("Sube o pega tu contenido, visualízalo, edítalo y usa un asistente de IA para refinarlo. Finalmente, descarga tu documento en formato Markdown.")

# --- PANELES PRINCIPALES ---
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
                    xls = pd.ExcelFile(uploaded_file)
                    sheet_to_display = st.selectbox("Selecciona una hoja para visualizar", xls.sheet_names)
                    if sheet_to_display:
                        df = pd.read_excel(xls, sheet_name=sheet_to_display)
                        st.dataframe(df) # Muestra el dataframe original tal como se lee
                        
                        # Guarda todo el contenido del excel para procesarlo, aplicando la corrección
                        full_excel_text = []
                        for name in xls.sheet_names:
                            sheet_df = pd.read_excel(xls, sheet_name=name)
                            if not sheet_df.empty:
                                # --- LÍNEA CLAVE DE LA CORRECCIÓN ---
                                # Rellena las celdas vacías (NaN) con el valor de la celda superior
                                sheet_df.fillna(method='ffill', inplace=True)
                                
                                full_excel_text.append(f"## Hoja: {name}\n\n{sheet_df.to_markdown(index=False)}\n\n")
                        st.session_state.original_content = "".join(full_excel_text)
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
        # Actualiza el estado si el usuario edita manualmente
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
        
        # Muestra el historial del chat
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Entrada del usuario para el chat
        if instruction := st.chat_input("Da una instrucción para editar..."):
            # Añade el mensaje del usuario al historial
            st.session_state.chat_history.append({"role": "user", "content": instruction})
            with st.chat_message("user"):
                st.markdown(instruction)

            # Llama a la IA para que edite el documento
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
                    
                    # Actualiza el editor con el nuevo texto y limpia el historial para la próxima tarea
                    st.session_state.structured_text = response.text
                    st.session_state.chat_history = [] # Limpia el historial para la siguiente instrucción
                    st.rerun() # Refresca la app para mostrar los cambios en el editor

                except Exception as e:
                    st.error(f"Error al editar con la IA: {e}")
