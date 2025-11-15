# Use a Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .

# Install uv
RUN pip install uv

# Install any needed dependencies using uv
RUN uv pip install --no-cache-dir --system -r requirements.txt

# Copy the Streamlit app files
COPY strmlt/ .

# Expose the Streamlit port
EXPOSE 8501

# The command to run the Streamlit app
CMD ["streamlit", "run", "cal_demo.py"]
