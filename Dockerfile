# Versão do python do projeto.
FROM python:3.14.6-slim

# Evita a gravação de arquivos .pyc e força o log direto no terminal.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cria e define a pasta de trabalho dentro do container.
WORKDIR /app

# Copia as dependências e instala.
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o restante do código para dentro da máquina virtual.
COPY . /app/