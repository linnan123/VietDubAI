FROM python:3.12-slim
RUN set -eu; \
    export DEBIAN_FRONTEND=noninteractive; \
    printf '%s\n' \
        'Acquire::Retries "3";' \
        'Acquire::http::Timeout "30";' \
        'Acquire::https::Timeout "30";' \
        'APT::Update::Error-Mode "any";' \
        > /etc/apt/apt.conf.d/80-vietdub-network; \
    retry_apt() { \
        for attempt in 1 2 3; do \
            if "$@"; then return 0; else status=$?; fi; \
            if [ "$attempt" -eq 3 ]; then return "$status"; fi; \
            printf 'APT attempt %s failed (exit %s); retrying\n' "$attempt" "$status" >&2; \
            sleep "$((attempt * 5))"; \
        done; \
    }; \
    retry_apt apt-get update; \
    retry_apt apt-get install -y --no-install-recommends ffmpeg; \
    rm -rf /var/lib/apt/lists/*
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check --retries 6 --timeout 30 -r requirements.txt
COPY . .
RUN useradd --create-home app && mkdir -p /data && chown -R app:app /data /code
USER app
