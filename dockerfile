FROM python:3.11-slim

WORKDIR /app


COPY requirements.txt ./
COPY app.py ./
COPY templates/ ./templates/


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
