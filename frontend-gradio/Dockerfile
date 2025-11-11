FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY gradio_app.py .

# Expose Gradio port
EXPOSE 7860

# Set environment variable for backend API
ENV BACKEND_API_URL=http://backend:8000

# Run the application
CMD ["python", "gradio_app.py"]
