import streamlit as st

import google.generativeai as genai

import pandas as pd


import io


import json



# --- CONFIGURACIÓN DE LA PÁGINA ---

st.set_page_config(


    page_title="Taller de Datos RAG",


    page_icon="🛠️",


    page_title="Taller de Datos RAG v2",


    page_icon=" directing_traffic",

    layout="wide"

)



@@ -18,135 +18,147 @@

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


# Usamos el estado de la sesión para mantener los datos entre interacciones


if 'structured_text' not in st.session_state:


    st.session_state.structured_text = "El resultado aparecerá aquí."

if 'original_content' not in st.session_state:

    st.session_state.original_content = ""


if 'structured_text' not in st.session_state:


    st.session_state.structured_text = "El resultado estructurado por la IA aparecerá aquí..."


if 'chat_history' not in st.session_state:


    st.session_state.chat_history = []



# --- INTERFAZ DE LA APLICACIÓN ---


st.title("🛠️ Taller de Estructuración de Datos para IA (RAG)")


st.markdown("Sube o pega tu contenido, visualízalo, edítalo y usa un asistente de IA para refinarlo. Finalmente, descarga tu documento en formato Markdown.")


st.title(" directing_traffic Taller de Estructuración de Datos Dirigido por IA")


st.markdown("Carga tu documento, dale instrucciones a la IA sobre cómo procesarlo y obtén un resultado estructurado y consistente.")




# --- PANELES PRINCIPALES ---


col1, col2, col3 = st.columns([1, 1, 1])


col1, col2 = st.columns(2, gap="large")




# --- COLUMNA 1: ENTRADA Y VISUALIZACIÓN ---


# --- COLUMNA 1: ENTRADA E INSTRUCCIONES ---

with col1:


    with st.container(border=True):


        st.subheader("1. Carga y Visualiza")


        


    st.subheader("1. Carga tu Documento")


    with st.container(border=True, height=300):

        input_method_tab, file_upload_tab = st.tabs(["Pegar Texto", "Subir Archivo Excel"])




        with input_method_tab:


            text_input = st.text_area("Pega texto sin formato aquí", height=150)


            text_input = st.text_area("Pega texto aquí", height=200)

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


                        st.dataframe(df)


                        # Guarda todo el contenido del excel para procesarlo


                        full_excel_text = []


                        for name in xls.sheet_names:


                            sheet_df = pd.read_excel(xls, sheet_name=name)


                            if not sheet_df.empty:


                                full_excel_text.append(f"## Hoja: {name}\n\n{sheet_df.to_markdown(index=False)}\n\n")


                        st.session_state.original_content = "".join(full_excel_text)


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




        if st.button("Procesar y Estructurar", use_container_width=True, type="primary"):


    with st.container(border=True, height=520):


        if process_button:

            if st.session_state.original_content:


                with st.spinner("🤖 Estructurando el documento inicial..."):


                with st.spinner("🤖 La IA está procesando el documento según tus instrucciones..."):

                    try:

                        model = genai.GenerativeModel('gemini-1.5-flash-latest')


                        generation_config = genai.types.GenerationConfig(


                            response_mime_type="application/json",


                            response_schema=SCHEMA


                        )


                        


                        user_instructions = instructions if instructions.strip() else "Procede con el análisis estándar."


                        

                        prompt = f"""


                        Analiza el siguiente texto y reestructúralo en formato Markdown. 


                        Crea un título, un resumen y secciones lógicas. Resalta los datos clave en negrita.


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


                        response = model.generate_content(prompt)


                        st.session_state.structured_text = response.text


                        st.success("¡Documento estructurado!")


                        


                        response = model.generate_content(prompt, generation_config=generation_config)


                        structured_json = json.loads(response.text)


                        st.session_state.structured_text = json_to_markdown(structured_json)


                        st.success("¡Documento procesado!")




                    except Exception as e:


                        st.error(f"Error en la estructuración inicial: {e}")


                        st.error(f"Ocurrió un error: {e}")


                        st.session_state.structured_text = "Error al procesar. Intenta con un texto o instrucción más clara."

            else:


                st.warning("Por favor, pega texto o sube un archivo.")


                st.warning("Por favor, carga un documento primero.")




# --- COLUMNA 2: EDITOR DE MARKDOWN ---


with col2:


    with st.container(border=True):


        st.subheader("2. Edita el Resultado")


        

        edited_text = st.text_area(


            "Puedes editar el texto directamente aquí",


            "Resultado en Markdown (puedes editarlo)",

            value=st.session_state.structured_text,


            height=500,


            key="editor"


            height=420

        )


        # Actualiza el estado si el usuario edita manualmente


        st.session_state.structured_text = edited_text





        

        st.download_button(

            label="📥 Descargar Archivo .md",


            data=st.session_state.structured_text,


            data=edited_text,

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
