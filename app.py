import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Estructurador de Datos RAG",
    page_icon="🏗️",
    layout="wide"
)

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (KeyError, FileNotFoundError):
    st.error("🚨 ¡Error de configuración! No se encontró la clave de API de Gemini.")
    st.warning("Por favor, configura el 'Secreto' de Streamlit llamado `GEMINI_API_KEY`.")
    st.stop()

# --- INTERFAZ DE LA APLICACIÓN ---
st.title("🏗️ Estructurador de Documentos para IA (RAG)")
st.markdown(
    "Pega texto sin formato o sube un archivo de Excel. La IA lo analizará y lo convertirá "
    "a formato **Markdown**, optimizado para bases de conocimiento RAG."
)

# Columnas para la entrada y el resultado
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("1. Proporciona tu Información")
        
        # Pestañas para elegir el método de entrada
        input_method_tab, file_upload_tab = st.tabs(["Pegar Texto", "Subir Archivo Excel"])

        with input_method_tab:
            unstructured_text = st.text_area(
                "Texto sin formato",
                height=350,
                placeholder="Pega aquí el contenido de un correo, un reporte, notas, etc."
            )
        
        with file_upload_tab:
            uploaded_file = st.file_uploader(
                "Sube un archivo .xlsx",
                type=['xlsx']
            )

        process_button = st.button("Estructurar Documento", type="primary", use_container_width=True)

with col2:
    with st.container(border=True):
        st.subheader("2. Resultado Estructurado (Markdown)")
        
        if 'structured_text' not in st.session_state:
            st.session_state.structured_text = "El resultado aparecerá aquí. Puedes editarlo antes de copiarlo."

        if process_button:
            source_text = ""
            # Prioriza el archivo subido si existe
            if uploaded_file is not None:
                try:
                    # Lee todas las hojas del archivo Excel
                    xls = pd.ExcelFile(uploaded_file)
                    full_text_parts = []
                    for sheet_name in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet_name)
                        # Ignora hojas vacías
                        if not df.empty:
                            full_text_parts.append(f"## Hoja: {sheet_name}\n\n")
                            # Convierte el dataframe a una tabla Markdown
                            full_text_parts.append(df.to_markdown(index=False))
                            full_text_parts.append("\n\n")
                    source_text = "".join(full_text_parts)
                    st.info(f"Archivo '{uploaded_file.name}' leído correctamente.")
                except Exception as e:
                    st.error(f"Error al procesar el archivo Excel: {e}")
            
            # Si no hay archivo, usa el texto pegado
            elif unstructured_text.strip():
                source_text = unstructured_text
            
            # Si no hay ninguna entrada, muestra una advertencia
            else:
                st.warning("Por favor, pega texto o sube un archivo para procesar.")
                source_text = None

            if source_text:
                with st.spinner("🤖 Analizando y reestructurando el texto..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        prompt = f"""
                        Tu tarea es actuar como un experto en gestión del conocimiento.
                        Analiza el siguiente texto, que puede ser texto plano o datos de una hoja de cálculo en formato Markdown. Tu objetivo es reestructurarlo en un documento Markdown claro y jerárquico, optimizado para una IA (RAG).

                        Sigue estas reglas estrictamente:
                        1.  **Crea un Título Principal:** Usa un encabezado de nivel 1 (`#`) para el tema general.
                        2.  **Genera un Resumen Ejecutivo:** Escribe un breve párrafo que resuma los puntos clave del documento.
                        3.  **Crea Secciones Lógicas:** Usa encabezados de nivel 2 (`##`) para los subtemas principales. Si los datos vienen de hojas de cálculo, usa los nombres de las hojas como guía.
                        4.  **Utiliza Listas:** Convierte enumeraciones o grupos de elementos en listas con viñetas (`-`).
                        5.  **Resalta Datos Clave:** Identifica y resalta la información más importante (nombres, fechas, cifras, conclusiones) usando texto en negrita (`**dato**`).
                        6.  **Sé Conciso:** Elimina redundancias. Mantén la esencia de la información.

                        --- TEXTO ORIGINAL ---
                        {source_text}
                        --- FIN DEL TEXTO ---
                        """
                        response = model.generate_content(prompt)
                        st.session_state.structured_text = response.text
                        st.success("¡Texto estructurado!")
                    except Exception as e:
                        st.error(f"Ocurrió un error al contactar a Gemini: {e}")
                        st.session_state.structured_text = "Error al procesar el texto."

        # El text_area permite al usuario editar el resultado
        st.text_area(
            "Resultado en Markdown (Editable)",
            value=st.session_state.structured_text,
            height=400,
            key="editable_result"
        )
