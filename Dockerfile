FROM python:3.11-alpine

# Add git
RUN apk update
RUN apk add git

# Install requirments
COPY ./requirements.txt ./app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Run
CMD python bot/main.py
