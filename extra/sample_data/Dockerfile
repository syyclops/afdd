# Use a multi-stage build to keep the final image size down
FROM python:3.11-buster as builder

# Install PostgreSQL client libraries
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install poetry
RUN pip install poetry

ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_USER=postgres
ENV POSTGRES_DB=postgres

# copies everything into container
COPY . /app

RUN poetry install

CMD ["poetry", "run", "sample_data"]