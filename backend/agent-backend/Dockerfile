FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Copy .env if you want to use local secrets (not recommended for production)
# COPY .env /app/.env

EXPOSE 5001

CMD ["python", "conversation_api.py"]