FROM python:3.11.7-slim-bookworm

RUN pip install --upgrade pip
WORKDIR /workdir
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["streamlit", "run", "main.py", "--server.port=8000"]
