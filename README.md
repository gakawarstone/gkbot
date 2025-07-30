Clone repo

    git clone https://github.com/gakawarstone/gkbot.git

Init project environment (set your credentials in .env)

    cp .env.dist .env

Run with uv

    uv sync --all-extras
    uv run bot

Or with docker-compose

    docker compose up

## Usage

### Makefile Scripts

The project includes several useful Makefile scripts:

- `make dev` - Run the bot in development mode with auto-reload
- `make test` - Run tests
- `make lint` - Run code linting
- `make format` - Format code with ruff
- `make debug` - Run tests in debug mode with pdb
- `make api` - Start the bot API service
- `make docker-update` - Update and restart Docker containers
- `make merge-to-master` - Merge current branch to master
- `make deploy` - Deploy by merging to master
- `make termux-build` - Build for Termux environment
- `make termux-run` - Run in Termux environment
