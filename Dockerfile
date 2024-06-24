# Use a multi-stage build to keep the final image size down
FROM python:3.11-buster as builder

# Install PostgreSQL client libraries
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /afdd

# Install poetry 
RUN pip install poetry

# copies everything into container
COPY . /afdd

RUN poetry install

CMD ["poetry", "run", "afdd"]