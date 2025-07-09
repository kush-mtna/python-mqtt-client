# Use a slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only what's needed
COPY app.py .
COPY index.html .
COPY requirements.txt .
COPY sparkplug_b_pb2.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the app port
EXPOSE 8000

# Start the app
CMD ["python", "app.py"]
