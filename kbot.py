import streamlit as st
import openai
import uuid
import time

# Inicialização da variável audio
audio = None
audio_on = False

from openai import OpenAI
client = OpenAI()

# Select the preferred model
MODEL = "gpt-4-1106-preview"

st.set_page_config(page_title="Kbot", page_icon="https://media.licdn.com/dms/image/C4D0BAQFU_zHiPt0UqQ/company-logo_200_200/0/1667941232492/kukac_logo?e=2147483647&v=beta&t=jrTrE3DIrNYM2hC70UE9lwJboIf4DFAHMUTuqGrOSxs")

# CSS para mudar a fonte para Dosis
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dosis:wght@400;500;600;700&display=swap');

html, body, [class*="st-"], h1, h2, h3, h4, h5, h6 {
    font-family: 'Dosis', sans-serif;
}            
            
}
                  
</style>
""", unsafe_allow_html=True)

#Controle de estados
if "session_id" not in st.session_state: # Used to identify each session
    st.session_state.session_id = str(uuid.uuid4())

if "run" not in st.session_state: # Stores the run state of the assistant
    st.session_state.run = {"status": None}

if "messages" not in st.session_state: # Stores the messages of the assistant
    st.session_state.messages = []

if "retry_error" not in st.session_state: # Used for error handling
    st.session_state.retry_error = 0

# Inicializar last_processed_message_id
if "last_processed_message_id" not in st.session_state:
    st.session_state.last_processed_message_id = None

#Esconder botão de expansão da imagem
hide_img_fs = '''
<style>
button[title="View fullscreen"]{
    visibility: hidden;}
</style>
'''
st.markdown(hide_img_fs, unsafe_allow_html=True)

#Configuração da página Streamlit
st.sidebar.write(" ")
st.sidebar.image('https://github.com/emidiosouza/estudo066_inovacao_kukac/blob/main/kbot.png?raw=true', width=280)
st.sidebar.header(":violet[Olá, eu sou Kbot, a Kukacker!]", divider='violet')
with st.sidebar: 	
    st.write("Fui treinada para te ajudar a resolver problemas do dia a dia da Kukac, agindo de acordo com nosso código de ética. Se precisar de ajuda, me conte o problema que está enfrentando e eu vou sugerir um plano de ação que você deve tomar para agir de acordo com nosso código.")
    st.link_button("Acesse o Código de Ética", "http://www.kukac.ai/codigodeetica")
    audio_on = st.toggle('ÁUDIO', help="Aqui você pode ligar e desligar a voz da assistente")
st.sidebar.header("", divider='violet')
st.sidebar.caption(':violet[Desenvolvido pela área de inovação da Kukac]')
st.sidebar.caption(':violet[Versão atual: 0.0.1]')

st.subheader(":violet[Como posso ajudar hoje?]", help="""
  # Deixe eu te dar alguns exemplos de questões em que eu posso ajudar:
  - Um cliente informou que não vai fazer o pagamento na data correta.
  - Recebi uma reclamação de um cliente sobre a demora na entrega de seu projeto.
  - Um de nossos colaboradores tem faltado constantemente ao trabalho e não entrega seus resultados no prazo.
""", divider='rainbow')


# Função para gerar áudio
def generate_audio_from_text(tts_text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=tts_text
    )
    # Salvar o arquivo de áudio
    audio_file_path = "audio_output.mp3"
    with open(audio_file_path, "wb") as file:
        file.write(response.content)
    return audio_file_path


#Configurações OpenAI
if "assistant" not in st.session_state:
    openai.api_key = st.secrets["OPENAI_API_KEY"]

    # Load the previously created assistant
    st.session_state.assistant = openai.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])

    # Create a new thread for this session
    st.session_state.thread = client.beta.threads.create(
        metadata={
            'session_id': st.session_state.session_id,
        }
    )

# Se a run anterior completar, ele carrega as mensagens.
elif hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed":
    # Retrieve the list of messages
    st.session_state.messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread.id
    )

# Mostrar fontes
    for thread_message in st.session_state.messages:
        for message_content in thread_message.content:
            # Access the actual text content
            message_content = message_content.text
            annotations = message_content.annotations
            citations = []
            
            # Iterate over the annotations and add footnotes
            for index, annotation in enumerate(annotations):
                # Replace the text with a footnote
                message_content.value = message_content.value.replace(annotation.text, f' [{index}]')
            
                # Gather citations based on annotation attributes
                if (file_citation := getattr(annotation, 'file_citation', None)):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
                elif (file_path := getattr(annotation, 'file_path', None)):
                    cited_file = client.files.retrieve(file_path.file_id)
                    citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
                    # Note: File download functionality not implemented above for brevity

            # Add footnotes to the end of the message before displaying to user
            message_content.value += '\n' + '\n'.join(citations)

 # Iterando nas mensagens para encontrar a última mensagem do bot
    if st.session_state.messages.data:
        for message in st.session_state.messages.data:
            if message.role == "assistant":
                ultima_mensagem = message
                break
            
        if ultima_mensagem and ultima_mensagem.content: # Verificando se a última mensagem do assistente foi encontrada
            if audio_on:
                audio_file_path = generate_audio_from_text(ultima_mensagem.content[0].text.value)          


# Mostrar mensagens na ordem reversa
    for message in reversed(st.session_state.messages.data):
        if message.role in ["user", "assistant"]:
            with st.chat_message(message.role):
                for content_part in message.content:
                    message_text = content_part.text.value
                    st.markdown(message_text)



# Pega input do usuário
if prompt := st.chat_input("Escreva aqui a sua mensagem."):
    with st.chat_message('user'):
        st.write(prompt)

    # Manda input para a thread
    st.session_state.messages = client.beta.threads.messages.create(
        thread_id=st.session_state.thread.id,
        role="user",
        content=prompt
    )

# Processa a thread
    st.session_state.run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread.id,
        assistant_id=st.session_state.assistant.id,
    )
    if st.session_state.retry_error < 3:
        time.sleep(1) # Wait 1 second before checking run status
        st.rerun()

# ERROR HANDLING
# Check if 'run' object has 'status' attribute
if hasattr(st.session_state.run, 'status'):
    # Handle the 'running' status
    if st.session_state.run.status == "running":
        with st.chat_message('assistant'):
            st.write("Thinking ......")
        if st.session_state.retry_error < 3:
            time.sleep(1)  # Short delay to prevent immediate rerun, adjust as needed
            st.rerun()

    # Handle the 'failed' status
    elif st.session_state.run.status == "failed":
        st.session_state.retry_error += 1
        with st.chat_message('assistant'):
            if st.session_state.retry_error < 3:
                st.write("Run failed, retrying ......")
                time.sleep(3)  # Longer delay before retrying
                st.rerun()
            else:
                st.error("FAILED: The OpenAI API is currently processing too many requests. Please try again later ......")

    # Handle any status that is not 'completed'
    elif st.session_state.run.status != "completed":
        # Attempt to retrieve the run again, possibly redundant if there's no other status but 'running' or 'failed'
        st.session_state.run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread.id,
            run_id=st.session_state.run.id,
        )
        if st.session_state.retry_error < 3:
            time.sleep(3)
            st.rerun()

    elif st.session_state.run.status == "completed":
        if audio_on:
            st.audio(audio_file_path, format='audio/mp3')
