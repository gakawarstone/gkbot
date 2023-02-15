Clone repo

    git clone https://github.com/gakawarstone/gkbot.git

Init project environment (set your credentials in .env)

    cp .env.dist > .env

Run with pipenv

    mkdir .venv
    pipenv sync
    pipenv run bot

Or with docker-compose

    docker compose up
