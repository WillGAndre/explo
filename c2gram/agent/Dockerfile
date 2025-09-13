FROM python:3.14.0rc2-alpine3.22

WORKDIR /opt

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libc-dev

COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/
COPY shared/ ./shared/
ENTRYPOINT [ "python", "-m", "agent.agent" ]