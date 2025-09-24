FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN wget https://github.com/jgm/pandoc/releases/download/3.1.8/pandoc-3.1.8-1-amd64.deb
RUN sudo dpkg -i pandoc-3.1.8-1-amd64.deb

RUN uv sync --frozen --no-cache

# ...existing code...
# Run the application using uv with --project
CMD ["uv", "--project", "ttsdocumentos_workers", "run", "task", "run", "iniciar_workers"]
