import base64
import os
from typing import MutableMapping, Optional, Tuple

import streamlit as st
from cryptography import fernet
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from streamlit_cookies_manager import CookieManager


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
            prefix: str = "",
            key_params_cookie="EncryptedCookieManager.key_params",
            ignore_broken=True,
    ):
        self._cookie_manager = CookieManager(path=path, prefix=prefix)
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