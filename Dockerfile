FROM python:3.11-slim

LABEL openenv=true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

ENV PORT 7860

EXPOSE 7860

CMD ["python", "app.py"]
