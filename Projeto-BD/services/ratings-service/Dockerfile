FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
RUN pip install requests

COPY application ./application

EXPOSE 8003

CMD ["uvicorn", "application.main:api", "--host", "0.0.0.0", "--port", "8000"]