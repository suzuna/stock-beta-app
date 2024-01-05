FROM python:3.11.7-slim-bookworm

RUN pip install --upgrade pip
WORKDIR /workdir
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
