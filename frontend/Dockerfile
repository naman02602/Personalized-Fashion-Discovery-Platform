# Pull the base docker image of python with tag 3.10.12
FROM python:3.10.12

# Change the working dir inside the container - cd /app
WORKDIR /app

# Copy main.py as source cod and req.txt as dependency
COPY . ./
COPY requirements.txt ./

# Install the dependency
RUN pip install --no-cache-dir -r requirements.txt

### Container Env same as local at this point
EXPOSE 8501

CMD ["streamlit", "run", "login_signup.py", "--server.port", "8501"]
