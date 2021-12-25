from datetime import datetime, timedelta
from pathlib import Path
from typing import MutableMapping, Mapping
from urllib.parse import unquote

import streamlit as st
from streamlit.components.v1 import components

build_path = Path(__file__).parent / 'build'
_component_func = components.declare_component("CookieManager.sync_cookies", path=str(build_path))


class CookieManager(MutableMapping[str, str]):
    def __init__(self, *, path: str = None, prefix=""):
        self._queue = st.session_state.setdefault('CookieManager.queue', {})
        self._prefix = prefix
        raw_cookie = self._run_component(save_only=False, key="CookieManager.sync_cookies")
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
            self._run_component(save_only=True, key="CookieManager.sync_cookies.save")

    def _run_component(self, save_only: bool, key: str):
        queue = {
            self._prefix + k: v for k, v in self._queue.items()
        }
        return _component_func(queue=queue, saveOnly=save_only, key=key)

    def _clean_queue(self):
        for name, spec in list(self._queue.items()):
            value = self._cookies.get(self._prefix + name)
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
        cookies = {
            k[len(self._prefix):]: v
            for k, v in self._cookies.items()
            if k.startswith(self._prefix)
        }
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
