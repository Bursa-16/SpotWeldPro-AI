FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt alembic.ini ./
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts
RUN chmod +x scripts/start.sh
CMD ["sh", "scripts/start.sh"]
