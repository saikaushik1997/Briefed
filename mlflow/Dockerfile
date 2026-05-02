FROM python:3.11-slim

RUN pip install --no-cache-dir mlflow psycopg2-binary

ENV MLFLOW_DISABLE_DNS_REBINDING_PROTECTION=true

EXPOSE 5050

CMD ["mlflow", "server", \
     "--host", "0.0.0.0", \
     "--port", "5050", \
     "--backend-store-uri", "/mlflow/tracking", \
     "--default-artifact-root", "/mlflow/artifacts", \
     "--allowed-hosts", "*", \
     "--cors-allowed-origins", "*"]
