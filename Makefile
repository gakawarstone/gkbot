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
	nodemon -e py -x $(PYTHON) bot/main.py

test:
	$(PYTHON) -m pytest

deploy: merge-to-master
