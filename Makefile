PYTHON = .venv/bin/python

termux-build:
	pkg install libiconv libxslt libxml2 rust binutils-is-llvm
	python -m venv env
	./env/bin/python install -r requirements.txt

termux-run:
	./env/bin/python bot/main.py

docker-update:
	git fetch && git pull
	docker compose stop && docker compose rm -f
	docker compose build
	docker compose up -d

merge-to-master:
	git push
	git checkout master
	git merge dev-3.0
	git push
	git checkout dev-3.0

api:
	docker compose -f services/bot-api/docker-compose.yml up -d

dev: api
	watchexec -r -e py $(PYTHON) bot/main.py

test:
	$(PYTHON) -m pytest --ignore services $(FILE)

deploy: merge-to-master

debug:
	$(PYTHON) -m pytest --ignore services/ --pdb $(FILE)

init-dev:
	uv sync --all-extras

lock-dev:
	uv pip freeze > requirements-dev.txt

lock:
	uv export --no-hashes --format requirements-txt > requirements.txt

lint:
	uvx ruff check . && uvx typos
