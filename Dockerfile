FROM python:3-alpine

WORKDIR /usr/src/app

RUN apk add \
      protobuf \
      make

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY proto/*.proto proto/
COPY Makefile .
RUN make chews

COPY . .

ENTRYPOINT ["python", "./chews.py", "--config_file", "/config/config.textproto"]
