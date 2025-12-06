FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create directory for database files (data storage)
RUN mkdir -p /app/data

# Run bot
CMD ["python", "main.py"]

