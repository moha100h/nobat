FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY scheduler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scheduler/ ./scheduler/
COPY shared/ ./shared/
CMD ["python","-m","scheduler.main"]
