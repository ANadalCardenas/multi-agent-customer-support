FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Runs the automated test suite by default.
# Override the command (e.g. `docker run <image> jupyter lab --ip=0.0.0.0 --allow-root`)
# to explore the notebooks instead.
CMD ["pytest"]
