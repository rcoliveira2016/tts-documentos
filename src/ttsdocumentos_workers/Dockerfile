FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN sudo apt-get install pandoc
RUN uv sync --frozen --no-cache

# ...existing code...
# Run the application using uv with --project
CMD ["uv", "--project", "ttsdocumentos_workers", "run", "task", "run", "iniciar_workers"]
