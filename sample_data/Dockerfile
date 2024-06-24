# Use a multi-stage build to keep the final image size down
FROM python:3.11-buster as builder

# Install PostgreSQL client libraries
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app
RUN pip install -r requirements.txt

# copies everything into container
COPY . /app

CMD ["python", "-m", "sample_data.create_sample_data"]