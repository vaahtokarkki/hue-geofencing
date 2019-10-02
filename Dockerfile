FROM balenalib/raspberry-pi-debian-python:3.7

RUN [ "cross-build-start" ]
WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install tcpdump
RUN apt-get install bluez

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]
RUN [ "cross-build-end" ]