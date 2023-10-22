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
