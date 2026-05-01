FROM python:3.11-slim

RUN pip install --no-cache-dir mlflow==2.18.0 psycopg2-binary

EXPOSE 5050

CMD ["mlflow", "server", \
     "--host", "0.0.0.0", \
     "--port", "5050", \
     "--backend-store-uri", "/mlflow/tracking", \
     "--default-artifact-root", "/mlflow/artifacts"]
