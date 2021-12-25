version = $(shell poetry version -s)

python_sources = $(wildcard streamlit_cookies_manager/*.py) pyproject.toml MANIFEST.in
js_sources := $(wildcard streamlit_cookies_manager/public/*) $(wildcard streamlit_cookies_manager/src/*) streamlit_cookies_manager/tsconfig.json
js_npm_install_marker = streamlit_cookies_manager/node_modules/.package-lock.json

build: streamlit_cookies_manager/build/index.html sdist wheels

sdist: dist/streamlit-cookies-manager-$(version).tar.gz
wheels: dist/streamlit_cookies_manager-$(version)-py3-none-any.whl

js: streamlit_cookies_manager/build/index.html

dist/streamlit-cookies-manager-$(version).tar.gz: $(python_sources) js
	poetry build -f sdist

dist/streamlit_cookies_manager-$(version)-py3-none-any.whl: $(python_sources) js
	poetry build -f wheel

streamlit_cookies_manager/build/index.html: $(js_sources) $(js_npm_install_marker)
	cd streamlit_cookies_manager && npm run build

$(js_npm_install_marker): streamlit_cookies_manager/package.json streamlit_cookies_manager/package-lock.json
	cd streamlit_cookies_manager && npm install

clean:
	-rm -r -f dist/* streamlit_cookies_manager/build/*
