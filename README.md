# Data Processing Pipeline — README Técnico

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![Python](https://img.shields.io/badge/python-%3E%3D3.12-brightgreen)](https://www.python.org/) [![Docker](https://img.shields.io/badge/docker-%3E%3D20.10-blue)](https://www.docker.com/)

Pipeline de processamento de dados conteinerizado, construído com FastAPI, RabbitMQ, Azurite (emulador do Azure Blob) e processos worker. Este repositório demonstra uma arquitetura modular (ingest → extract → normalize → TTS → finalize), infraestrutura como código para desenvolvimento local, gerenciamento reprodutível de ambientes com `uv` e orquestração de tarefas via `taskipy`.

---

## Índice

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Pré-requisitos](#pré-requisitos)
3. [Layout do Repositório](#layout-do-repositório)
4. [Instalação e Configuração](#instalação-e-configuração)
5. [Execução (containerizada)](#execução-containerizada)
6. [Tasks disponíveis (`taskipy`)](#tasks-disponíveis-taskipy)
7. [Fluxo de Desenvolvimento (local)](#fluxo-de-desenvolvimento-local)
8. [Integração: `uv`, Docker e `taskipy` ](#integração-uv-docker-e-taskipy)
9. [Solução de Problemas (Troubleshooting)](#solução-de-problemas-troubleshooting)
10. [Apêndice — Arquivos importantes](#apêndice---arquivos-importantes)

---

## Visão geral da arquitetura

Componentes principais:

- `api` (FastAPI) — ponto de entrada HTTP que recebe documentos (PDF/DOCX/EPUB). Faz upload do arquivo original para o Blob (Azurite em dev) e publica uma mensagem no RabbitMQ para iniciar o pipeline.
- `rabbitmq` — broker de mensagens que desacopla a API dos workers e garante entrega confiável entre estágios.
- `azurite` — emulador local do Azure Blob usado para persistir arquivos de entrada e artefatos gerados durante o desenvolvimento.
- `workers` — processos assíncronos que consomem mensagens, executam estágios do pipeline (extração de texto → normalização → TTS → finalização) e persistem resultados.
- `ttsdocumentos_lib_core` — biblioteca compartilhada com utilitários (storage, configuração, logging, serviços) usada por API e workers.

Fluxo simplificado:

1. Cliente envia documento → `api` armazena no Blob e publica mensagem em `rabbitmq`.
2. Worker de extração (`extract_text`) baixa o blob, extrai texto e publica no próximo tópico/queue.
3. Worker de normalização (`normalize_text`) limpa/segmenta o texto e publica para a fila de TTS.
4. Worker de TTS sintetiza áudio (modelos locais em `/models`) e armazena artefatos no blob.
5. Worker de finalização marca o job como concluído (persistência de metadados, notificações, etc.).

Arquitetura desacoplada facilita isolamento de falhas, escalabilidade independente e inspeção/telemetria por estágio.

---

## Pré-requisitos

- SO: Linux / macOS / Windows WSL
- Python: `>=3.12`
- Docker: `>=20.10` (recomenda-se Compose v2 compatível)
- `uv` — gerenciador de workspace e ambientes por subprojeto (obrigatório para este repositório)
- `taskipy` — utilitário de tarefas usado como dependência de desenvolvimento (definido em `src/pyproject.toml`)

Instalação recomendada do `uv` (uso de `uv` é a prática sugerida neste projeto; não usaremos `pipx` como recomendação):

```bash
# Instalar uv no ambiente do usuário
python -m pip install --user uv
# ou (ambiente virtual)
python -m pip install uv
```

Instale `taskipy` como ferramenta de desenvolvimento quando necessário (por exemplo no ambiente do repositório):

```bash
python -m pip install --user taskipy
```

> Observação: a documentação e os scripts deste projeto assumem execução via `uv` para garantir ambientes isolados por subprojeto e boa integração com editores (VSCode).

---

## Layout do repositório (resumo)

Principais entradas:

```
README.md
src/
  docker-compose.yml            # Compose de infra local
  pyproject.toml                # metadados do projeto + [tool.taskipy.tasks]
  ttsdocumentos_api/
    Dockerfile
    main.py                     # entrada FastAPI
  ttsdocumentos_workers/
    main.py                     # entrada dos workers
  ttsdocumentos_lib_core/       # biblioteca compartilhada
models/                         # modelos usados pelo TTS
azurite/                        # dados persistidos do Azurite (dev)
```

---

## Instalação e configuração

1. Clone o repositório:

```bash
git clone <seu-repo-url> && cd <repo-root>
```

2. Instale `uv` conforme indicado na seção de pré-requisitos.

3. Sincronize os ambientes do workspace e instale dependências. IMPORTANTE: execute com `--all-packages` para que o VSCode e outros editores obtenham IntelliSense completo para todos os subprojetos:

```bash
uv sync --all-packages
```

Esse comando cria ambientes por subprojeto conforme definido em `src/pyproject.toml` e garante resolução correta de dependências para a IDE.

Antes de abrir o código no editor, recomendo abrir o diretório de subprojetos para que o `uv` e as extensões (Python/IntelliSense) detectem corretamente os ambientes por subprojeto. A forma mais direta é abrir o VSCode apontando para a pasta `src`:

```bash
code ./src
```

Abrir o VSCode em `./src` faz com que a árvore de projetos fique centrada nos subprojetos (`ttsdocumentos_api`, `ttsdocumentos_workers`, `ttsdocumentos_lib_core`) e melhora a integração com `uv` e as configurações de workspace.

4. Levante a infraestrutura local (RabbitMQ + Azurite + API) usando o `docker-compose` fornecido em `src/docker-compose.yml` (execute a partir da raiz do repositório):

```bash
docker-compose -f src/docker-compose.yml up -d
```

---

## Execução (containerizada)

O `src/docker-compose.yml` do projeto define os seguintes serviços (resumo):

- `rabbitmq` — `rabbitmq:3-management` (portas `5672`, `15672`)
- `azurite` — `mcr.microsoft.com/azure-storage/azurite` (portas `10000`, `10001`, `10002`)
- `api` — imagem construída a partir de `ttsdocumentos_api/Dockerfile`, exposta em `8085:80`

Comandos úteis:

```bash
docker-compose -f src/docker-compose.yml up -d

docker-compose -f src/docker-compose.yml down

docker-compose -f src/docker-compose.yml up -d --build api

docker-compose -f src/docker-compose.yml logs -f api
```

Pontos de verificação:

- RabbitMQ UI: `http://localhost:15672` (user/pass padrão: `guest`/`guest`)
- Azurite endpoint Blob: `http://localhost:10000`
- API: `http://localhost:8085`

---

## Tasks disponíveis (`taskipy`) — extraído de `src/pyproject.toml`

As tasks definidas em `src/pyproject.toml` (seção `[tool.taskipy.tasks]`) são usadas como atalhos de desenvolvedor. As strings abaixo são usadas exatamente no arquivo de configuração:

```
[tool.taskipy.tasks]
api = "uv --project ttsdocumentos_api run fastapi dev ttsdocumentos_api/main.py"
iniciar_workers = "uv --project ttsdocumentos_workers run ./ttsdocumentos_workers/main.py"
```

Descrição das tasks:

- `api`
  - Comando: `uv --project ttsdocumentos_api run fastapi dev ttsdocumentos_api/main.py`
  - Propósito: Inicia o servidor FastAPI da subaplicação `ttsdocumentos_api` em modo de desenvolvimento (com reload quando aplicável).

- `iniciar_workers`
  - Comando: `uv --project ttsdocumentos_workers run ./ttsdocumentos_workers/main.py`
  - Propósito: Executa o runner dos workers que processam mensagens das filas.

Execução das tasks (opções):

- Usando `taskipy` (se instalado):

```bash
# a partir da raiz do repositório
task api
# ou
task iniciar_workers
```

- Recomenda-se executar via `uv` para garantir que cada subprojeto use seu ambiente isolado:

```bash
uv run task api
uv run task iniciar_workers
```

- Chamadas diretas (strings iguais às definidas nas tasks):

```bash
uv --project ttsdocumentos_api run fastapi dev ttsdocumentos_api/main.py
uv --project ttsdocumentos_workers run ./ttsdocumentos_workers/main.py
```

---

## Fluxo de desenvolvimento (local)

Passos recomendados para desenvolvimento diário:

1. Levante a infra local se necessário:

```bash
docker-compose -f src/docker-compose.yml up -d
```

2. Garanta que os ambientes estejam sincronizados (apenas após mudanças em `pyproject.toml` ou na primeira vez):

```bash
uv sync --all-packages
```

Recomenda-se abrir o VSCode apontando para a pasta `src` depois do `uv sync` para que as extensões (Python, Pylance) encontrem os ambientes criados por `uv`:

```bash
code ./src
```

3. Execute a API em modo desenvolvimento (com hot-reload quando aplicável):

```bash
uv --project ttsdocumentos_api run fastapi dev ttsdocumentos_api/main.py
# ou via task
uv run task api
```

4. Em um terminal separado, execute os workers para processar jobs:

```bash
uv run task iniciar_workers
# ou
uv --project ttsdocumentos_workers run ./ttsdocumentos_workers/main.py
```

5. Ao editar `ttsdocumentos_lib_core`, é comum reiniciar a API/workers para que as alterações sejam carregadas. Para desenvolvimento iterativo, prefira rodar a API com o runner que suporta reload.

---

## Integração: `uv`, Docker e `taskipy`

- `uv` cria ambientes por subprojeto conforme `src/pyproject.toml` (`[tool.uv.workspace].members`). Isso isola dependências e garante que cada subprojeto tenha seu próprio interpretador e bibliotecas.
- `taskipy` apenas expõe comandos definidos em `pyproject.toml` de forma consistente. Neste projeto, as tasks delegam a execução para `uv` com as strings exatas mostradas acima.
- `docker-compose` (arquivo `src/docker-compose.yml`) provê a infraestrutura necessária (RabbitMQ, Azurite e API) para replicar um ambiente próximo ao de produção em desenvolvimento local.

Fluxo recomendado:

1. `docker-compose -f src/docker-compose.yml up -d` — sobe infraestrutura (RabbitMQ, Azurite, API).
2. `uv sync --all-packages` — provisiona ambientes por subprojeto e habilita IntelliSense para IDEs.
3. `uv run task api` / `uv run task iniciar_workers` — executa serviços dentro dos ambientes gerenciados por `uv`.

---

## Solução de problemas (selecionados)

- Portas em uso
  - Verifique se nenhuma outra aplicação usa `5672`, `15672`, `10000` ou `8085`. Use `lsof -i :15672` e finalize o processo conflitante ou ajuste `src/docker-compose.yml`.

- Conectividade Azurite
  - A variável `AZURE_STORAGE_CONNECTION_STRING` definida no `src/docker-compose.yml` aponta para `http://azurite:10000/devstoreaccount1;`. Ao rodar a API localmente (fora de container) ajuste para `http://localhost:10000/...` se necessário.

- `uv` / IntelliSense ausente
  - Rode `uv sync --all-packages`. Caso o comando não exista, instale `uv` com `python -m pip install --user uv` ou dentro de um virtualenv.

- `task` não encontrado
  - Instale `taskipy` ou execute diretamente via `uv` (recomendado): `uv run task <nome>`.

- Erros de conexão RabbitMQ
  - Confirme `RABBITMQ_DEFAULT_USER`/`RABBITMQ_DEFAULT_PASS` no `src/docker-compose.yml` (padrão `guest`/`guest`) e que `RABBITMQ_HOST` em `api` aponta para `rabbitmq`.

---

## Apêndice — Arquivos importantes

- `src/docker-compose.yml` — Compose para `rabbitmq`, `azurite`, `api`.
- `src/pyproject.toml` — metadados, `[tool.uv.workspace]` e `[tool.taskipy.tasks]` (tasks do projeto).

Trecho relevante de `src/pyproject.toml`:

```
[tool.taskipy.tasks]
api = "uv --project ttsdocumentos_api run fastapi dev ttsdocumentos_api/main.py"
iniciar_workers = "uv --project ttsdocumentos_workers run ./ttsdocumentos_workers/main.py"
```

---

## Resumo rápido (cheat-sheet)

```bash
# 1. Clone
git clone <repo> && cd <repo>

# 2. Instale uv e sincronize ambientes
python -m pip install --user uv
uv sync --all-packages

# Abra o VSCode na pasta dos subprojetos para melhor integração com uv
code ./src

# 3. Levante infra
docker-compose -f src/docker-compose.yml up -d

# 4. Execute API (dev)
uv run task api
# ou
uv --project ttsdocumentos_api run fastapi dev ttsdocumentos_api/main.py

# 5. Execute workers
uv run task iniciar_workers
# ou
uv --project ttsdocumentos_workers run ./ttsdocumentos_workers/main.py
```

---

Se desejar, posso agora:
- Gerar `docs/ARCHITECTURE.md` com fluxograma e sequência de eventos;
- Incluir `docker-compose.override.yml` para desenvolvimento com volumes montados;
- Adicionar configurações de workspace do VSCode para mapear ambientes `uv` automaticamente.

Diga qual opção prefere que eu implemente em seguida.