.PHONY: all
all:
	./venv/bin/python ./generate.py

.PHONY: setup
setup:
	virtualenv-3 ./venv
	./venv/bin/pip install -r requirements.txt


.PHONY: clean
clean:
	rm -rf build/*
	rm -rf output/*
	rm -rf docs/modules.md

# keep rpm target out to restore original Makefile

# drop update-specs to restore original Makefile

.PHONY: update
update:all
	git pull --rebase origin main
	git add --all .
	git commit -m "up" || echo "No changes to commit"
	git push
	git checkout specs
