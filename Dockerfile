FROM python:3.12-slim

WORKDIR /app

# Copy code and install dependencies
COPY . /app
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Expose FastAPI port
EXPOSE 8000

# Run the app
CMD ["python", "app.py"]
