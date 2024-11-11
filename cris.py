""" Analista de Crédito Virtual para Mútua """
from globals import *
from tools import *
logd("Iniciando a aplicação")
# Ler o arquivo .env
try:
    # Tenta carregar as variáveis de ambiente
    if not load_dotenv():
        raise EnvironmentError("Arquivo .env não encontrado ou falha ao carregar.")
except EnvironmentError as e:
    loge(f"Erro ao carregar o arquivo .env: {e}")
    print("A operação load_dotenv() não foi bem-sucedida. O programa não pode continuar.")
    sys.exit(1)  # Encerra o programa com um código de erro

audio_saida_bytes = BytesIO()

# para usar o grog para transcrição de audios para texto
client = Groq()

# configuração do eleven labs texto para audio
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client_eleven = ElevenLabs(api_key=ELEVENLABS_API_KEY,)
ELEVENLABS_API_KEY_RUDOLPH = os.getenv("ELEVENLABS_API_KEY_RUDOLPH")
client_eleven_rudolph = ElevenLabs(api_key=ELEVENLABS_API_KEY_RUDOLPH,)

# Configuração da página
st.set_page_config(page_title="Eu te Escuto", page_icon="🤖", layout="wide")

success_placeholder = st.empty()

# função para salvar e encerrar a sessão
def salvar_e_encerrar():
    """    salvar a conversa """
    logd("Salvando e encerrando a sessão ...")
    resultado_salvar = salvar_registro(str(st.session_state.chat_history))
    if resultado_salvar[0]:
        success_placeholder.success("Dados salvos com sucesso! 🚀 ✅")
        logd("Sucesso")
    else:
        success_placeholder.error(f"Erro na gravação {resultado_salvar[1]}")
        logd("Falha na gravação dos dados do diálogo")
    st.session_state.clear()  # Limpa o estado da sessão
    streamlit_js_eval(js_expressions="parent.window.location.reload()")   # Reinicializa a página

# Função para obter a resposta do bot
def get_response(user_query, chat_history, tipollm = 'gemini'):
    """ função de consult ao llm """
    #
    # definindo qual prompt usar
    #
    logd("Consultando LLM")
    if tipollm == 'gemini':
        arquivo_template = 'prompt_concessao_gemini.txt'
    elif tipollm == 'gpt':
        arquivo_template = 'prompt_concessao_gpt.txt'

    with open(arquivo_template) as arquivo:
        template = arquivo.read()    
    prompt = ChatPromptTemplate.from_template(template)
    if tipollm == 'gemini': 
        llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        safety_settings={HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE},
        temperature=1.0,
        frequence_penalty=10,
        top_p=0.9,
        max_tokens=100,
        )
    elif tipollm == 'gpt':
        llm = ChatOpenAI(temperature=1.0, model="gpt-4o",model_kwargs={"frequency_penalty":2.0},
                         openai_api_key=os.getenv("OPENAI_API_KEY"))
        
    chain = prompt | llm | StrOutputParser()
    try:
        resp = chain.invoke({"chat_history": chat_history,"user_question": user_query,})
    except Exception as e:
        loge(str(e))    
        raise Exception(f"Erro no LLM: {str(e)}")
    return resp

# Estrutura do cabeçalho
logd("Iniciando cabeçalho html")
st.markdown(
    """
    <div class="header">
        <h1> Converse comigo. Sou a Cris. Seu assistente para concessão de Benefícios da Mútua </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Inicialização do estado da sessão
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

audio_query = None
texto_query = None
query = None

logd("Criando a side bar")
# Entrada do usuário no rodapé
with st.sidebar:
    # Carregar a imagem
    try:
        image_path = "./crisa600.png" # Substitua pelo caminho correto 
        image = Image.open(image_path)
        st.image(image,caption = 'Cris (Gerente)',width=250, use_column_width=False)
    except Exception as e:
        loge(F"Não foi possível carregar a imagem do bot {str(e)}. Continuando sem imagem ")

    # Entrada do usuário
    logd("Solicitando audio")
    audio_input = st.experimental_audio_input("Registre sua mensagem em áudio ...")
    logd("Solicitando texto")
    texto_query = st.chat_input("Digite a sua mensagem aqui ...", key="user_input")
    logd(f"texto_query: {texto_query}")
    if st.button("Clique aqui para Salvar/Encerrar"):
        salvar_e_encerrar()
    opcao_sintese_audio = st.radio(
        "Síntese de Áudio:",
        ("Google", "Eleven Labs")
    )
    opcao_llm = st.radio(
        "Motor de LLM:",
        ("Básico", "Avançado")
    )
    if opcao_llm == 'Básico':
        tipollm = 'gemini'
    else:
        tipollm = 'gpt'
    try:
        if audio_input:
            logd("processando audio da entrada do usuário")
            audio_bytes = audio_input.getvalue()
            audio_file = BytesIO(audio_bytes)
            transcription = client.audio.transcriptions.create(
                file=("audio.wav", BytesIO(audio_bytes)), # Required audio file
                model="whisper-large-v3", # Required model to use for transcription
                prompt="Specify context or spelling",  # Optional
                response_format="json",  # Optional
                language="pt",  # Optional
                temperature=0.0  # Optional
            )
            audio_query = transcription.text
        else:
            logd("Audio vazio")
    except Exception as e:
        loge(f"Erro ao processar o audio: {str(e)}")
        audio_query = None

if texto_query:
    query = texto_query
elif audio_query:
    query = audio_query
if query:
    logd("Contactando o LLM")
    st.session_state.chat_history.append(HumanMessage(content=query))
    for i in range(TENTATIVAS_MAXIMAS_LLM):
        logd(f"Tentativa {i+1} de {TENTATIVAS_MAXIMAS_LLM}")
        dup = False
        try:        
            # pegar a resposta do LLM    
            resposta = get_response(query, st.session_state.chat_history,tipollm) # gpt ou gemini
            logd(f"Resposta do LLM: {resposta[:10]}")
            response_text = tratar_texto(resposta)
            logd(f"Mensagem recebida e tratada: {response_text[:20]} ")    
            # laco de teste das respostas
            for m in st.session_state.chat_history:
                if response_text.lower() in str(m).lower() or m.content == response_text or response_text == None or response_text == "":
                    logd("Resposta duplicada ou não fornecida")
                    dup = True
                    time.sleep(DELAY_PERGUNTAS)
                    continue
            if not dup: 
                logd("Resposta aceita")
                break
        except Exception as e:
            loge(f"Erro ao obter resposta do LLM: {str(e)}")
            time.sleep(DELAY_PERGUNTAS)
    else:
        loge("Limite de tentativas atingido")   
    if dup: 
        response_text = random.choice(RESPOSTAS_DISSUASIVAS)
    st.session_state.chat_history.append(AIMessage(content=response_text))
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                if "$" in message.content:
                    st.write(message.content.replace('$', '\\$'))
                else:
                    st.write(message.content)
        else:
            with st.chat_message("Human"):
                if "$" in message.content:
                    st.write(message.content.replace('$', '\\$'))
                else:
                    st.write(message.content)
    logd(f"Sintetizando texto {opcao_sintese_audio[:10]} como audio no {opcao_sintese_audio} ")
    if response_text and opcao_sintese_audio == 'Google':
        try:
            myobj = gTTS(text=response_text, lang='pt', slow=False)
            myobj.write_to_fp(audio_saida_bytes)
            logd("reproduzindo audio")  
            st.audio(audio_saida_bytes, format='audio/mp3',autoplay=True)
        except Exception as e:
            loge(f"Erro ao sintetizar o audio no google: {str(e)}")

    elif response_text and opcao_sintese_audio == 'Eleven Labs':
        try:
            response = client_eleven_rudolph.text_to_speech.convert(
                #voice_id="cyD08lEy76q03ER1jZ7y", # ScheilaSMTy
                voice_id="cgSgspJ2msm6clMCkdW9", # Jessica
                output_format="mp3_22050_32",
                text=response_text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.0,
                    similarity_boost=1.0,
                    style=0.0,
                    use_speaker_boost=True,
                ),
            )
            for chunk in response:
                if chunk:
                    audio_saida_bytes.write(chunk)
            audio_saida_bytes.seek(0)
            logd("reproduzindo audio")  
            st.audio(audio_saida_bytes, format='audio/mp3',autoplay=True)
        except Exception as e:
            loge(f"Erro ao sintetizar o audio eleven labs : {str(e)}")     
    
