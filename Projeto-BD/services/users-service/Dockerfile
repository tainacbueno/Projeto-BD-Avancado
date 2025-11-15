FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY application ./application

EXPOSE 8001

CMD ["uvicorn", "application.main:api", "--host", "0.0.0.0", "--port", "8000"]