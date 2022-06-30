FROM gakawarstone/pipenv


# Copy files
COPY . ./app

WORKDIR /app

# [ ] Database
# Add dependencies and run bot
RUN pipenv sync
RUN pipenv run bot 