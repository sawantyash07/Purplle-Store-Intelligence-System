FROM python:3.11-slim
WORKDIR /srv
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt
COPY app ./app
RUN mkdir -p /data
ENV STORE_INTEL_DB=/data/store_intelligence.db
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

