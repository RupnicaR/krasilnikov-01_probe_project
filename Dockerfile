FROM python:3.12-alpine AS build

WORKDIR /app
RUN apk add --no-cache build-base postgresql-dev mariadb-connector-c-dev pkgconf
RUN python -m venv /venv
COPY requirements.txt .
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.12-alpine

WORKDIR /app
RUN apk add --no-cache libpq mariadb-connector-c
COPY --from=build /venv /venv
COPY app.py .
ARG VERSION
RUN echo "$VERSION" > /app/VERSION
ENV PATH=/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1
STOPSIGNAL SIGINT
CMD ["python", "app.py"]
