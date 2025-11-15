# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install uv
RUN pip install uv

# Install any needed dependencies using uv
RUN uv pip install --no-cache-dir --system -r requirements.txt

# Copy the application code
COPY ./api /app/api

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "api.cal_api:app", "--host", "0.0.0.0", "--port", "8000"]

