FROM python:3.14.0rc2-alpine3.22

WORKDIR /opt

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libc-dev

COPY controller/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY controller/ ./controller/
COPY shared/ ./shared/
ENTRYPOINT [ "python", "-m", "controller.controller" ]