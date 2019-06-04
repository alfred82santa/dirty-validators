PACKAGE_NAME = dirty-validators
PACKAGE_COVERAGE = dirty_validators

help:
	@echo "Options"
	@echo "---------------------------------------------------------------"
	@echo "help:                     This help"
	@echo "requirements-test:        Download requirements for tests"
	@echo "requirements-docs:        Download requirements for docs"
	@echo "run-tests:                Run tests with coverage"
	@echo "publish:                  Publish new version on Pypi"
	@echo "clean:                    Clean compiled files"
	@echo "flake:                    Run Flake8"
	@echo "prepush:                  Helper to run before to push to repo"
	@echo "autopep:                  Reformat code using PEP8"
	@echo "---------------------------------------------------------------"

requirements-test:
	@echo "Installing $(PACKAGE_NAME) tests requirements..."
	pip install -r requirements-test.txt

requirements-docs:
	@echo "Installing $(PACKAGE_NAME) docs requirements..."
	pip install -r requirements-docs.txt

run-tests:
	@echo "Running tests..."
	nosetests --with-coverage -d --cover-package=$(PACKAGE_COVERAGE) --cover-erase -x

publish: clean build
	@echo "Publishing new version on Pypi..."
	twine upload dist/*

build:
	@echo "Build package..."
	python3 setup.py bdist_wheel

clean:
	@echo "Cleaning compiled files..."
	find . | grep -E "(__pycache__|\.pyc|\.pyo)$ " | xargs rm -rf
	@echo "Cleaning distribution files..."
	rm -rf dist
	@echo "Cleaning build files..."
	rm -rf build
	@echo "Cleaning egg info files..."
	rm -rf ${PACKAGE_NAME}.egg-info
	@echo "Cleaning coverage files..."
	rm -f .coverage

flake:
	@echo "Running flake8 tests..."
	flake8 $(PACKAGE_COVERAGE)
	flake8 tests

autopep:
	autopep8 --max-line-length 120 -r -j 8 -i .

prepush: flake run-tests

