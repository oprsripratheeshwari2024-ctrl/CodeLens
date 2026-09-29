FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r backend/requirements.txt
WORKDIR /app/backend
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
