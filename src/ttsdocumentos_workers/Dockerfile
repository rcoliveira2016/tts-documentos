FROM python:3.12-slim

# Instala dependências básicas para baixar e instalar o .deb
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Instala Pandoc
RUN wget https://github.com/jgm/pandoc/releases/download/3.1.8/pandoc-3.1.8-1-amd64.deb
RUN dpkg -i pandoc-3.1.8-1-amd64.deb || apt-get install -f -y

# Instala NumPy
RUN pip install --no-cache-dir numpy

# Copia uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copia a aplicação
COPY . /app
WORKDIR /app

# Instala NumPy via uv e sincroniza o projeto
RUN uv add numpy \
    && uv sync --frozen --no-cache

# Comando de execução

CMD ["uv",  "run", "task", "iniciar_workers"]
