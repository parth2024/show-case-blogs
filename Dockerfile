# Use official Python image
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files (optional)
RUN python manage.py collectstatic --noinput || true

# Expose the port to Railway
EXPOSE $PORT

# Start Gunicorn and bind to $PORT
CMD ["sh", "-c", "gunicorn daycare.wsgi:application --bind 0.0.0.0:$PORT"]
