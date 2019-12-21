.DEFAULT_GOAL = install
.PHONY = install

env:
	python -m venv env

install: env
	source env/bin/activate && pip install -U pip
	source env/bin/activate && pip install -r requirements.txt
	source env/bin/activate && pip install -r requirements-dev.txt

package: install
	@rm -rf dist/
	@mkdir dist
	@source env/bin/activate && python setup.py clean sdist bdist_wheel


upload:
	source env/bin/activate && twine upload dist/*


