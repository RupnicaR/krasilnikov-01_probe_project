FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py README.md .
ARG VERSION=dev
RUN printf '%s\n' "$VERSION" > /app/VERSION
ENV APP_PORT=5001
ENV PYTHONDONTWRITEBYTECODE=1
EXPOSE 5001
CMD ["python", "app.py"]
