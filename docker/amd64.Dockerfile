FROM python:3.7-slim-buster

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get -y install tcpdump bluez

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]