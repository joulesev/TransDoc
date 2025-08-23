import streamlit as st
import google.generativeai as genai

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Estructurador de Datos RAG",
    page_icon="🏗️",
    layout="wide"
)

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
# Asegúrate de haber configurado el secreto GEMINI_API_KEY en tu app de Streamlit
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (KeyError, FileNotFoundError):
    st.error("🚨 ¡Error de configuración! No se encontró la clave de API de Gemini.")
    st.warning(
        "Por favor, configura el 'Secreto' de Streamlit llamado `GEMINI_API_KEY`."
    )
    st.stop()

# --- INTERFAZ DE LA APLICACIÓN ---
st.title("🏗️ Estructurador de Documentos para IA (RAG)")
st.markdown(
    "Pega texto sin formato de cualquier fuente. La IA lo analizará y lo convertirá "
    "a formato **Markdown**, optimizado para bases de conocimiento RAG."
)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("1. Pega tu Texto Original")
        unstructured_text = st.text_area(
            "Texto sin formato",
            height=400,
            placeholder="Pega aquí el contenido de un correo, un reporte, notas, etc."
        )
        
        process_button = st.button("Estructurar Documento", type="primary", use_container_width=True)

with col2:
    with st.container(border=True):
        st.subheader("2. Resultado Estructurado (Markdown)")
        
        if 'structured_text' not in st.session_state:
            st.session_state.structured_text = "El resultado aparecerá aquí. Puedes editarlo antes de copiarlo."

        if process_button:
            if not unstructured_text.strip():
                st.warning("Por favor, introduce texto para procesar.")
                st.session_state.structured_text = "Esperando texto..."
            else:
                with st.spinner("🤖 Analizando y reestructurando el texto..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        prompt = f"""
                        Tu tarea es actuar como un experto en gestión del conocimiento.
                        Analiza el siguiente texto y reestructúralo completamente en formato Markdown. Tu objetivo es crear un documento claro, jerárquico y fácil de procesar para una futura IA (RAG).

                        Sigue estas reglas estrictamente:
                        1.  **Identifica el Título Principal:** Usa un encabezado de nivel 1 (`#`) para el tema general del documento.
                        2.  **Crea Secciones Lógicas:** Usa encabezados de nivel 2 (`##`) para los subtemas principales.
                        3.  **Utiliza Listas:** Convierte cualquier enumeración o grupo de elementos en listas con viñetas (`-`).
                        4.  **Resalta Datos Clave:** Identifica y resalta la información más importante (nombres, fechas, cifras, conclusiones) usando texto en negrita (`**dato**`).
                        5.  **Sé Conciso:** Elimina redundancias y texto de relleno. Mantén la esencia de la información.
                        6.  **No Inventes Información:** Basa tu estructura únicamente en el texto proporcionado.

                        --- TEXTO ORIGINAL ---
                        {unstructured_text}
                        --- FIN DEL TEXTO ---
                        """
                        response = model.generate_content(prompt)
                        st.session_state.structured_text = response.text
                        st.success("¡Texto estructurado!")
                    except Exception as e:
                        st.error(f"Ocurrió un error al contactar a Gemini: {e}")
                        st.session_state.structured_text = "Error al procesar el texto."

        # El text_area permite al usuario editar el resultado antes de usarlo
        st.text_area(
            "Resultado en Markdown (Editable)",
            value=st.session_state.structured_text,
            height=400,
            key="editable_result"
        )