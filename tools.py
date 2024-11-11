""" Ferramentas para acesso ao banco de dados e o LLM """
import sqlite3
import re,json
from globals import *
load_dotenv()
# Conecta ao banco de dados SQLite (será criado se não existir)
try:
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    # Cria a tabela, se ainda não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        renda_mensal INTEGER,
        credito_solicitado INTEGER,
        garantias TEXT,
        status_cliente TEXT,
        historico_inadimplencia TEXT,
        risco TEXT)
    """)
    conn.commit()
finally:
    conn.close()

def calcular_risco_credito(renda_mensal, credito_solicitado, garantias=[], status_cliente='sim', inadimplente='sim'):
    """
    Calcula o score de crédito com base em:
    - Renda mensal e capacidade de pagamento
    - Histórico de crédito
    - Garantias e patrimônio
    - Relacionamento com a instituição

    Parâmetros:
    - renda_mensal (float): Renda mensal do cliente.
    - credito_solicitado (float): Valor do crédito solicitado.
    - garantias (list): Lista de dicionários com nome e valor das garantias.
      Exemplo: [{"tipo": "imóvel", "valor": 100000}, {"tipo": "veículo", "valor": 50000}]
    - status_cliente (str): "sim" ou "não" indicando se é cliente existente.
    - historico_inadimplencia (str): "sim" ou "não" indicando se há histórico de inadimplência.

    Retorno:
    - float: Score de crédito calculado.
    """
    # Pesos para cada fator
    w_R = 0.4  # Renda e Capacidade de Pagamento
    w_H = 0.3  # Histórico de Crédito
    w_G = 0.2  # Garantias e Patrimônio
    w_L = 0.1  # Relacionamento com a Instituição

    # Fator R: Renda e Capacidade de Pagamento
    try:
        proporcao_divida = credito_solicitado / renda_mensal
    except Exception as e:
        print("Erro no calculo ",e )
        proporcao_divida = 1
    if proporcao_divida < 0.3:
        R = 90
    elif proporcao_divida < 0.5:
        R = 70
    else:
        R = 50

    # Fator H: Histórico de Crédito
    if inadimplente.lower() == "não":
        H = 90
    else:
        H = 50

    # Fator G: Garantias e Patrimônio
    try:
        valor_total_garantias = sum(garantia["valor"] for garantia in list(garantias))
    except Exception as e:
        print("Erro no calculo das garantias ",e )
        valor_total_garantias = 0
    
    if valor_total_garantias >= credito_solicitado:
        G = 90
    elif valor_total_garantias > 0:
        G = 70
    else:
        G = 50

    # Fator L: Relacionamento com a Instituição
    if status_cliente.lower() == "sim":
        L = 80
    else:
        L = 50

    # Cálculo do score de crédito
    score_credito = (R * w_R) + (H * w_H) + (G * w_G) + (L * w_L)

    # retornando o risco

    if score_credito >= 80:
        return "baixo"
    elif 60 <= score_credito < 80:
        return "moderado"
    return "alto"

def parse_numero(numero_str):
    if isinstance(numero_str, float) or isinstance(numero_str, int):
        return float(numero_str)
    # Verifica e converte se o número está no formato brasileiro (ex: 20.000,00)
    if re.match(r"^\d{1,3}(\.\d{3})*,\d{2}$", numero_str):
        numero_str = numero_str.replace('.', '').replace(',', '.')
    
    # Verifica e converte se o número está no formato americano com vírgulas (ex: 20,000.00)
    elif re.match(r"^\d{1,3}(,\d{3})*\.\d{2}$", numero_str):
        numero_str = numero_str.replace(',', '')
    
    # Verifica e converte se o número está no formato americano sem vírgulas (ex: 20000.00)
    elif re.match(r"^\d+\.\d{2}$", numero_str):
        numero_str = numero_str  # formato americano já é compatível
    
    # Verifica se é um número inteiro ou decimal (ex: 30 ou 30.2)
    elif re.match(r"^\d+(\.\d+)?$", numero_str):
        pass  # já é um número válido, só converte para float
    
    # Verifica se é um número no formato brasileiro com vírgula decimal (ex: 30,2 ou 300000,2)
    elif re.match(r"^\d+(\.\d{3})*,\d+$", numero_str):
        numero_str = numero_str.replace(',', '.')
    
    else:
        raise ValueError("Formato de número inválido")
    
    # Converte a string para float e retorna
    return float(numero_str)

def interpretar_mensagens_brutas(texto):
    """  Expressão regular para capturar o conteúdo dentro de content='...' """
    padrao = r"content='(.*?)'"  # Captura o conteúdo entre aspas simples
    mensagens = re.findall(padrao, texto, re.DOTALL)  # Captura múltiplas linhas
    return mensagens

def extrair_json_de_string(string: str):
    """ extrair o json das respostas da llm """
    print("string recebida para extrair json ",string )
    try:
        dados = json.loads(string)
        return dados
    except Exception:
        loge("json não pode ser convertido diretamente ") # apenas sinaliza problema no json
    try:
        # Expressão regular para encontrar o conteúdo entre as primeiras { e }
        padrao = r"\{.*?\}"
        correspondencia = re.search(padrao, string, re.DOTALL)
        if correspondencia:
            # Extrai o JSON e converte para um dicionário
            json_str = correspondencia.group(0)
            dados = json.loads(json_str)
            return dados
        else:
            print("Nenhum JSON encontrado na string.")
            return None
    except json.JSONDecodeError as e:
        loge(f"Erro ao decodificar JSON: {e}")
        return None
    
def diagnostico_credito(dialogo : str):
    """ fazer o diagnostico finaceiro do solicitante """   
    arquivo_template = 'prompt_analise_dialogo.txt'
    with open(arquivo_template) as arquivo:
        template = arquivo.read() 
        
    prompt = ChatPromptTemplate.from_template(template)
    #llm = ChatOpenAI()
    llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    safety_settings={HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE},
    temperature=1.0,
    frequence_penalty=2,
    )
    chain = prompt | llm | StrOutputParser()
    try:
        resp = chain.invoke({"texto": dialogo,})
    except Exception as e:
        resp = "No momento estou sem condições de continuar a conversa. Tente novamente em seguida"
        loge(str(e))
    return resp

def salvar_registro(historico: str):
    """ corigir isso aqui para calcular os campos necessários """
    mensagens = "\n".join(interpretar_mensagens_brutas(historico))
    json_resposta = extrair_json_de_string(diagnostico_credito(mensagens))
    print("Mensagens apos extracao de json ", json_resposta)
    try:
        nome = json_resposta["nome"]
        if nome == None or nome == "":
            nome = "Anônimo"
    except Exception as e:
        loge(f"Erro no json nome {str(e)} : {json_resposta}")
        nome = "Anônimo"
    try:
        renda_mensal = parse_numero(json_resposta["renda_mensal"])
    except Exception as e:
        loge(f"Erro no json renda {str(e)} : {json_resposta}")
        renda_mensal = 0.0
    try:
        valor_credito = parse_numero(json_resposta["valor_credito"])
    except Exception as e:
        loge(f"Erro no json credito {str(e)} : {json_resposta}")
        valor_credito = 0.0
    try:
        garantias = str(json_resposta["garantias"])
    except Exception as e:
        loge(f"Erro no json garantias {str(e)} : {json_resposta}")
        garantias = "[]"
    try:
        cliente_existente = str(json_resposta["cliente_existente"])
    except Exception as e:
        loge(f"Erro no json cliente {str(e)} : {json_resposta}")
        cliente_existente = "não"
    try:
        inadimplente = str(json_resposta["inadimplente"])
    except Exception as e:
        loge(f"Erro no json inadimplente {str(e)} : {json_resposta}")
        inadimplente = "não"   
    risco = calcular_risco_credito(renda_mensal, valor_credito, garantias, cliente_existente,inadimplente)
    with sqlite3.connect(BANCO_DADOS) as conn:
        conn.execute(""" INSERT INTO registros (nome, renda_mensal, credito_solicitado, garantias,
                     status_cliente,historico_inadimplencia, risco) VALUES (?, ?, ?, ?, ?, ?, ? ) """, 
                       (nome, renda_mensal, valor_credito, garantias, cliente_existente, inadimplente, risco))
        return (True,"")
    return (False, f"Erro: {e}") 

def listar_registros():
    """ retornar os registros gravados no banco de dados """
    with sqlite3.connect(BANCO_DADOS) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registros")
        registros = cursor.fetchall()
        return {"registros": registros}
    return None

def remover_texto_entre_asteriscos(texto):
    return re.sub(r'\*.*?\*', '', texto)

def remover_human_message(texto):
    # Expressão regular para remover 'HumanMessage(...)', ignorando maiúsculas/minúsculas
    return re.sub(r'humanmessage\([^)]*\)', '', texto, flags=re.IGNORECASE)

def remover_ai_message(texto):
    # Remove as partes indesejadas da mensagem
    texto = texto.replace("AIMessagecontent='", "")
    texto = texto.replace("', additional_kwargs=, response_metadata=", "")
    return texto

def remover_message_content(texto):
    # Remove as partes indesejadas da mensagem
    texto = texto.replace("Messagecontent='", "")
    return texto

def remover_resposta_chatbot(texto):
    # Expressão regular para remover 'ChatbotMessage(...)', ignorando maiúsculas/minúsculas
    return re.sub(r'Resposta do Chatbot\([^)]*\)', '', texto, flags=re.IGNORECASE)   

def remover_cris_inicio(texto):
    # Expressão regular para remover 'glenda' do início da string, ignorando maiúsculas e minúsculas
    return re.sub(r'^cris\s*', '', texto, flags=re.IGNORECASE)

def tratar_texto(response_text):
    response_text = response_text.replace(']','')
    response_text = response_text.replace('[','')
    response_text = response_text.replace('{','')
    response_text = response_text.replace('}','')
    response_text = response_text.replace(':','')
    response_text = response_text.replace('*','')
    response_text = response_text.replace('!','')
    response_text = response_text.replace('(','')
    response_text = response_text.replace(')','')
    response_text = response_text.replace('ofensa','')
    trecho1 = "(aqui você irá colocar a variável com o nome do solicitante)"
    response_text = response_text.replace(trecho1,'')   
    response_text = remover_human_message(response_text) 
    response_text = remover_ai_message(response_text) 
    response_text = remover_message_content(response_text) 
    response_text = remover_resposta_chatbot(response_text)
    response_text = remover_cris_inicio(response_text)    
    return remover_texto_entre_asteriscos(response_text)
