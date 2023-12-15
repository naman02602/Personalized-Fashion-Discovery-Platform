# Use a base image with Python
FROM python:3.10.12

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend folders and any necessary files into the container
COPY module /app/module
COPY fastapi_service /app/fastapi_service
COPY databaseTeam4 /app/databaseTeam4
COPY routers /app/routers
COPY main.py /app/

EXPOSE 8000

# Set the command to run your FastAPI app
CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]