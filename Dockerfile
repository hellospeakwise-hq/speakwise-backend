# Use an official Python runtime as a parent image
FROM python:3.12-slim-bullseye AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements/ /app/requirements/
RUN pip install uv \
    && uv pip install --system -r requirements/production.txt

# Final stage
FROM python:3.12-slim-bullseye

# Create a non-root user
RUN addgroup --system django && \
    adduser --system --group django

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set work directory
WORKDIR /app

# Copy installed python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

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
