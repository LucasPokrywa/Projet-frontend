FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY . .
CMD ["python", "-m", "flask", "--app", "app", "run", "--host=0.0.0.0"]