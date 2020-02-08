FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY meross_proxy /app/meross_proxy/

CMD ["python", "-m", "meross_proxy"]
EXPOSE 8080
