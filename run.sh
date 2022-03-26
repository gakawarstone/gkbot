#!/bin/bash
if [[ $1 == --check ]]; then
    if [ -d logs ]; then
        echo "logs exists"
    else 
        echo "making logs directory..." && mkdir logs
    fi

    if [ -f .env ]; then
        echo "enviromental variables exists"
    else
        echo "FAILED .env file not exists"
        exit
    fi

    if [ -f data/bot.sqlite ]; then
        echo "sqlite db file exist"
    else
        echo "creating sqlite db file..." && cat data/create_pomodoro.sql | sqlite3 data/bot.sqlite 
    fi
fi

pipenv run python main.py &>> logs/runtime.log &

