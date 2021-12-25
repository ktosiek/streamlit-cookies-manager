from collections import Mapping, MutableMapping
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

import streamlit as st
from streamlit.components.v1 import components

build_path = Path(__file__).parent / 'build'
_component_func = components.declare_component("CookieManager.sync_cookies", path=str(build_path))


class CookieManager(MutableMapping[str, str]):
    def __init__(self):
        self._queue = st.session_state.setdefault('CookieManager.queue', {})
        raw_cookie = _component_func(queue=self._queue, saveOnly=False, key="CookieManager.sync_cookies")
        if raw_cookie is None:
            self._cookies = None
        else:
            self._cookies = parse_cookies(raw_cookie)
            self._clean_queue()
        self._default_expiry = datetime.now() + timedelta(days=365)

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
                path='/',
            )

    def __delitem__(self, key: str) -> None:
        if key in self._cookies:
            self._queue[key] = dict(value=None, path='/')

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
