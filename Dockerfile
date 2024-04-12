#**************************************
# MIT License
# Dockerfile to run the ddns.py script
#**************************************

FROM python:3.10-bullseye

WORKDIR /usr/src/app
RUN apk update
RUN apk add nano
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD [ "python", "./ddns.py" ]
