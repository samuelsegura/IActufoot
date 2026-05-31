FROM python:3.12.13-slim
WORKDIR /app
COPY pyproject.toml .
COPY actufoot/ actufoot/
RUN pip install --no-cache-dir .
CMD ["actufoot"]
