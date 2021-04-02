FROM balenalib/raspberry-pi2-debian-python:3.9

RUN [ "cross-build-start" ]
WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get -y install tcpdump bluez iputils-ping

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]
RUN [ "cross-build-end" ]