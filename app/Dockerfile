FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app
COPY requirements.txt /app/

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
