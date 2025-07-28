# Best Practice: Start from a slim base image to keep the container small and secure.
# This explicitly sets the platform, as requested in the challenge guidelines.
FROM --platform=linux/amd64 python:3.10-slim-bullseye

# Best Practice: Set a working directory.
WORKDIR /app

# Best Practice: Install dependencies in their own layer.
# Use --no-cache-dir to prevent pip from storing a cache, reducing the final image size.
RUN pip install --no-cache-dir PyMuPDF

# Copy only the necessary application code into the container.
COPY ./process_pdfs.py /app/process_pdfs.py

# Specify the command to run your application.
CMD ["python", "process_pdfs.py"]


# To build image 

# docker build --platform linux/amd64 -t pdf-processor .


# To run the container

# docker run --rm \
#   -v "$(pwd)/sample_dataset/pdfs:/app/input:ro" \
#   -v "$(pwd)/sample_dataset/outputs:/app/output" \
#   --network none \
#   pdf-processor
