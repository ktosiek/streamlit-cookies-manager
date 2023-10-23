
rm -r dist
virtualenv -p python3.10 .venv
python3 -m pip install --upgrade twine build

cd streamlit_cookies_manager
export NODE_OPTIONS=--openssl-legacy-provider
yarn install
yarn build
cd ..

poetry build
python3 -m twine upload --repository pypi --skip-existing dist/*
rm -r dist

