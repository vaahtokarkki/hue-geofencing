FROM balenalib/raspberry-pi-python:3.7

RUN [ "cross-build-start" ]
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]
RUN [ "cross-build-end" ]