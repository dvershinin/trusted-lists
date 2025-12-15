.PHONY: all
all:
	./venv/bin/python ./generate.py

.PHONY: setup
setup:
	virtualenv-3 ./venv
	./venv/bin/pip install -r requirements.txt

.PHONY: setup-dev
setup-dev: setup
	./venv/bin/pip install pytest pytest-mock responses ruff pre-commit
	./venv/bin/pre-commit install

.PHONY: test
test:
	./venv/bin/python -m pytest tests/ -v

.PHONY: lint
lint:
	./venv/bin/python -m ruff check .


.PHONY: clean
clean:
	rm -rf build/*
	rm -rf output/*
	rm -rf docs/modules.md

.PHONY: update
update:
	git fetch origin
	git checkout -f main
	git reset --hard origin/main
	$(MAKE) all
	git add build/ src/ trusted.yml
	git commit -m "up" || echo "No changes to commit"
	git push origin main

.PHONY: specs-publish
specs-publish:
	git fetch origin
	# switch to specs, create if doesn't exist
	git checkout specs 2>/dev/null || git checkout -b specs || exit 1
	# ensure we start from remote state
	git reset --hard origin/specs || true
	# check out files built from main to specs (mirror)
	git checkout main -- build
	git checkout main -- src
	git checkout main -- Makefile
	git checkout main -- settings.yml
	# generate top-level specs and copy XMLs if changed
	for f in build/*.xml; do \
		name=$$(basename "$$f" .xml); \
		if [ ! -f "$$name.xml" ] || ! diff -q "$$f" "$$name.xml" >/dev/null; then \
			VERSION=$$(date --utc +%Y%m%d); \
			/bin/cp -f "$$f" ./; \
			./venv/bin/jinja2 src/ipset.spec.j2 "build/$$name.yml" -D version=$$VERSION --outfile="firewalld-ipset-$$name.spec"; \
		fi; \
	done
	# regenerate CircleCI config using buildstrap (reads settings.yml)
	python3 ~/Projects/buildstrap/generate_circleci_config.py --project-dir .
	# commit only when there are staged changes
	git add -- *.spec *.xml .circleci settings.yml 2>/dev/null || true
	git diff --cached --quiet || git commit -m "Up"
	# push specs branch
	git push origin specs
	# return to main so next invocations use the main Makefile/targets
	git checkout -f main

.PHONY: circleci-update
circleci-update:
	git fetch origin
	git checkout -f main
	git reset --hard origin/main
	# run your updater that expands newer distros and writes .circleci config
	"$(HOME)"/scripts/update-circle.sh trusted-lists generated_config_specs_only.yml
	# include updated CI config
	git add .circleci
	git commit -m "Update CircleCI config" || echo "No CircleCI changes"
	git push origin main

.PHONY: publish
publish: circleci-update update specs-publish
