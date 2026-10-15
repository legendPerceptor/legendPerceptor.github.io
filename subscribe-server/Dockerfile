FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    HOST=0.0.0.0 \
    PORT=8080

WORKDIR /srv/subscribe

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY cli.py ./
COPY docker-entrypoint.py /usr/local/bin/docker-entrypoint.py

RUN useradd --system --uid 10001 --create-home appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data /srv/subscribe
# NOTE: no `USER appuser` here on purpose. The entrypoint starts as root, fixes
# the ownership of a bind-mounted /data (Docker-created directories belong to
# root inside the container), then drops to `appuser` before exec'ing the app.

VOLUME ["/data"]
EXPOSE 8080

ENTRYPOINT ["python3", "/usr/local/bin/docker-entrypoint.py"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
