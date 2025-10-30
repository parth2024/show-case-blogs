# Use official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Run collectstatic (optional)
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD ["sh", "-c", "gunicorn daycare.wsgi:application --bind 0.0.0.0:$PORT"]
