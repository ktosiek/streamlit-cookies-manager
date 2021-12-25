import base64
import os
from collections import Mapping, MutableMapping
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import unquote

import streamlit as st
from cryptography import fernet
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from streamlit.components.v1 import components

build_path = Path(__file__).parent / 'build'
_component_func = components.declare_component("CookieManager.sync_cookies", path=str(build_path))


@st.cache
def key_from_parameters(salt: bytes, iterations: int, password: str):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )

    return base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))


class EncryptedCookieManager(MutableMapping[str, str]):
    def __init__(
            self, *,
            password: str,
            path: str = None,
            key_params_cookie="EncryptedCookieManager.key_params",
            ignore_broken=True,
    ):
        self._cookie_manager = CookieManager(path=path)
        self._fernet: Optional[Fernet] = None
        self._key_params_cookie = key_params_cookie
        self._password = password
        self._ignore_broken = ignore_broken

    def ready(self):
        return self._cookie_manager.ready()

    def save(self):
        return self._cookie_manager.save()

    def _encrypt(self, value):
        self._setup_fernet()
        return self._fernet.encrypt(value)

    def _decrypt(self, value):
        self._setup_fernet()
        return self._fernet.decrypt(value)

    def _setup_fernet(self):
        if self._fernet is not None:
            return
        key_params = self._get_key_params()
        if not key_params:
            key_params = self._initialize_new_key_params()
        salt, iterations, magic = key_params
        key = key_from_parameters(
            salt=salt,
            iterations=iterations,
            password=self._password
        )

        self._fernet = Fernet(key)

    def _get_key_params(self) -> Optional[Tuple[bytes, int, bytes]]:
        raw_key_params = self._cookie_manager.get(self._key_params_cookie)
        if not raw_key_params:
            return
        try:
            raw_salt, raw_iterations, raw_magic = raw_key_params.split(':')
            return base64.b64decode(raw_salt), int(raw_iterations), base64.b64decode(raw_magic)
        except (ValueError, TypeError):
            print(f"Failed to parse key parameters from cookie {raw_key_params}")
            return

    def _initialize_new_key_params(self) -> Tuple[bytes, int, bytes]:
        salt = os.urandom(16)
        iterations = 390000
        magic = os.urandom(16)
        self._cookie_manager[self._key_params_cookie] = b':'.join([
            base64.b64encode(salt),
            str(iterations).encode('ascii'),
            base64.b64encode(magic)
        ]).decode('ascii')
        return salt, iterations, magic

    def __repr__(self):
        if self.ready():
            return f'<EncryptedCookieManager: {dict(self)!r}>'
        return '<EncryptedCookieManager: not ready>'

    def __getitem__(self, k: str) -> str:
        try:
            return self._decrypt(self._cookie_manager[k].encode('utf-8')).decode('utf-8')
        except fernet.InvalidToken:
            if self._ignore_broken:
                return
            raise

    def __iter__(self):
        return iter(self._cookie_manager)

    def __len__(self):
        return len(self._cookie_manager)

    def __setitem__(self, key: str, value: str) -> None:
        self._cookie_manager[key] = self._encrypt(value.encode('utf-8')).decode('utf-8')

    def __delitem__(self, key: str) -> None:
        del self._cookie_manager[key]


class CookieManager(MutableMapping[str, str]):
    def __init__(self, *, path: str = None):
        self._queue = st.session_state.setdefault('CookieManager.queue', {})
        raw_cookie = _component_func(queue=self._queue, saveOnly=False, key="CookieManager.sync_cookies")
        if raw_cookie is None:
            self._cookies = None
        else:
            self._cookies = parse_cookies(raw_cookie)
            self._clean_queue()
        self._default_expiry = datetime.now() + timedelta(days=365)
        self._path = path if path is not None else "/"

    def ready(self) -> bool:
        return self._cookies is not None

    def save(self):
        if self._queue:
            _component_func(queue=self._queue, saveOnly=True, key="CookieManager.sync_cookies.save")

    def _clean_queue(self):
        for name, spec in list(self._queue.items()):
            value = self._cookies.get(name)
            if value == spec['value']:
                del self._queue[name]

    def __repr__(self):
        if self.ready():
            return f'<CookieManager: {dict(self)!r}>'
        return '<CookieManager: not ready>'

    def __getitem__(self, k: str) -> str:
        return self._get_cookies()[k]

    def __iter__(self):
        return iter(self._get_cookies())

    def __len__(self):
        return len(self._get_cookies())

    def __setitem__(self, key: str, value: str) -> None:
        if self._cookies.get(key) != value:
            self._queue[key] = dict(
                value=value,
                expires_at=self._default_expiry.isoformat(),
                path=self._path,
            )

    def __delitem__(self, key: str) -> None:
        if key in self._cookies:
            self._queue[key] = dict(value=None, path=self._path)

    def _get_cookies(self) -> Mapping[str, str]:
        if self._cookies is None:
            raise CookiesNotReady()
        cookies = self._cookies
        for name, spec in self._queue.items():
            if spec['value'] is not None:
                cookies[name] = spec['value']
            else:
                cookies.pop(name, None)
        return cookies


def parse_cookies(raw_cookie):
    cookies = {}
    for part in raw_cookie.split(';'):
        part = part.strip()
        if not part:
            continue
        name, value = part.split('=', 1)
        cookies[unquote(name)] = unquote(value)
    return cookies


class CookiesNotReady(Exception):
    pass
