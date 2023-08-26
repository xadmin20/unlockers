# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container to /app
WORKDIR /app

# Install Git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

# Create and set working directory
WORKDIR /app

# Install Python dependencies
COPY req.txt /app
RUN pip install --no-cache-dir -r req.txt
RUN pip install gunicorn

# Add the rest of the code
COPY . /app
COPY env/Lib/site-packages/postie /usr/local/lib/python3.10/site-packages/postie
COPY env/Lib/site-packages/des /usr/local/lib/python3.10/site-packages/des
COPY env/Lib/site-packages/solo /usr/local/lib/python3.10/site-packages/solo

# Add user
RUN useradd -ms /bin/bash newuser

# Create directories and set permissions
RUN mkdir -p /app/static/admin/js
RUN chown -R newuser:newuser /app
RUN chmod -R 777 /app

USER newuser

# Collect static files
RUN python manage.py collectstatic --noinput

# Run Gunicorn
CMD ["gunicorn", "unlockers.wsgi:application", "--bind", "0.0.0.0:8000"]
