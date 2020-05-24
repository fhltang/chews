FROM python:3

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        protobuf-compiler \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY proto/*.proto proto/
COPY Makefile .
RUN make chews

COPY . .

ENTRYPOINT ["python", "./chews.py"]