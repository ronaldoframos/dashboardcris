""" dados globais usandos pelos scrips """
import os, sys, time, logging, requests, random
from io import BytesIO
# import uuid
import streamlit as st                          # type: ignore
from streamlit_js_eval import streamlit_js_eval # type: ignore
from langchain_core.messages import AIMessage, HumanMessage # type: ignore
from langchain_core.prompts import ChatPromptTemplate       # type: ignore
from langchain_core.output_parsers import StrOutputParser   # type: ignore  JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI,HarmCategory,HarmBlockThreshold # type: ignore
from langchain_openai import ChatOpenAI         # type: ignore
from dotenv import load_dotenv                  # type: ignore
from PIL import Image                           # type: ignore
import requests                                 # type: ignore
from gtts import gTTS                           # type: ignore
from elevenlabs import VoiceSettings            # type: ignore
from elevenlabs.client import ElevenLabs        # type: ignore
from groq import Groq                           # type: ignore

# cuidando dos logs
# Configurando o logger
logger = logging.getLogger("__name__")
logger.setLevel(logging.DEBUG)  # Define o nível de log

# Configuração do handler para salvar logs em um arquivo
file_handler = logging.FileHandler("logs.txt")
file_handler.setLevel(logging.DEBUG)

# Formato de log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Adicionando o handler ao logger
logger.addHandler(file_handler)
logi = lambda message: logger.info(message)
logw = lambda message: logger.warning(message)
logd = lambda message: logger.debug(message)
loge = lambda message: logger.error(message)
logc = lambda message: logger.critical(message)

# nome do banco de dados
BANCO_DADOS = "db_credito.db"

# numero de tentativas para obter resposta não duplicada do llm
TENTATIVAS_MAXIMAS_LLM = 10 
DELAY_PERGUNTAS = 5

RESPOSTAS_DISSUASIVAS = [
    "Peço perdão. Estou com problemas para responder a sua mensagem. Por favor, tente novamente.",
    "Desculpe, mas estou sem condições de continuar a conversa. Por favor, tente de novo.",
    "Desculpe, parece que nosso canal de comunicação está com problemas. Por favor, tente novamente.",
    "Mil desculpas, mas estou com problemas para responder a sua mensagem. Por favor, tente mais uma vez."
]