FROM python:3.12.13-slim
WORKDIR /app
COPY pyproject.toml .
COPY actufoot/ actufoot/
RUN pip install --no-cache-dir . \
    && useradd -r -u 1001 -s /sbin/nologin actufoot \
    && mkdir -p /data && chown actufoot:actufoot /data
USER actufoot
CMD ["actufoot"]
