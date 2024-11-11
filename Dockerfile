# app/Dockerfile
FROM python:3.12-slim
WORKDIR /
# Copia os arquivos do diretório atual para o contêiner
COPY . .
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN apt-get update && \ 
    apt-get install -y supervisor && \
    apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
EXPOSE 4333
EXPOSE 4343
HEALTHCHECK CMD curl --fail http://localhost:4333/_stcore/health
# Inicia o Supervisor para rodar ambos os scripts
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
