import os

import streamlit as st
from streamlit.components.v1 import html

from streamlit_cookies_manager import EncryptedCookieManager

# This should be on top of your script
cookies = EncryptedCookieManager(
    password=os.environ.get("COOKIES_PASSWORD", "My secret password"),
)
if not cookies.ready():
    # Wait for the component to load and send us current cookies.
    st.spinner()
    st.stop()

st.write("Current cookies:", dict(cookies))
html("""
    Raw cookie: <span id="raw-cookie"></span>
    <script>
    document.getElementById('raw-cookie').innerText = window.top.document.cookie
    </script>
""")
value = st.text_input("New value for a cookie")

col1, col2 = st.columns(2)
changed = False
with col1:
    if st.button("Change the cookie"):
        cookies['a-cookie'] = value
        changed = True
        assert cookies['a-cookie'] == value, \
            "CookieManager should return the target value, not the stale one"
with col2:
    if st.button("Delete the cookie"):
        del cookies['a-cookie']
        changed = True

if changed:
    "I'll save your cookie on next rerun."

    if st.button("No really, change it now"):
        cookies.save()  # Force saving the cookies now, without a rerun
