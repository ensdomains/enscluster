FROM python:3.6.4-stretch

WORKDIR /app
COPY metrics.py /app
COPY requirements.txt /app

RUN pip install -r requirements.txt

CMD python metrics.py
