FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies for psycopg2 and other tools
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
# Note: In production you might want to run this as part of the startup script or compose command
# RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Gunicorn is used as the production server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "aamyproject.wsgi:application"]
