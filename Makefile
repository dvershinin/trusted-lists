.PHONY: all
all:
	./venv/bin/python ./generate.py

.PHONY: setup
setup:
	virtualenv-3 ./venv
	./venv/bin/pip install -r requirements.txt


.PHONY: clean
clean:
	find docs/modules -type f -exec rm -f {} +
	rm -rf docs/modules.md

.PHONY: update
update:all
	git pull --rebase origin main
	git add --all .
	git commit -m "up"
	git push
	git checkout specs
