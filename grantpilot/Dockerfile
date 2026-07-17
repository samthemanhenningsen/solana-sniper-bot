FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY grantpilot ./grantpilot
COPY serve.py .

# Persist the SQLite DB outside the container: -v grantpilot-data:/data
ENV GRANTPILOT_DB=sqlite:////data/grantpilot.db
VOLUME /data

EXPOSE 8000
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]
