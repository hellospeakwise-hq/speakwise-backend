# Use an official Python runtime as a parent image
FROM python:3.14-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv \
    && uv sync --frozen --no-install-project

# Final stage
FROM python:3.14-slim

# Create a non-root user
RUN addgroup --system django && \
    adduser --system --group django

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    PATH="/app/.venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy installed python packages from builder
COPY --from=builder /app/.venv /app/.venv

# Copy project files
COPY . .

# Set ownership
RUN chown -R django:django /app

# Entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

USER django

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
