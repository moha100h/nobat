FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY master_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY master_bot/ ./master_bot/
COPY shared/ ./shared/
CMD ["python","-m","master_bot"]
