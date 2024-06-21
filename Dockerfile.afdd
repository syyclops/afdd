# Use a multi-stage build to keep the final image size down
FROM python:3.11-buster as builder

# Install PostgreSQL client libraries
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the files needed for the poetry installation
RUN touch README.md

WORKDIR /afdd

# Install any needed packages specified in requirements.txt
COPY requirements.txt /afdd
RUN pip install -r requirements.txt

# copies everything into container
COPY . /afdd

CMD ["python", "main.py"]