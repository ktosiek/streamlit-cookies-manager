import streamlit as st
from streamlit.components.v1 import html

from streamlit_cookies_manager import CookieManager

# This should be on top of your script
cookies = CookieManager()
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
if st.button("Change the cookie"):
    cookies['a-cookie'] = value
    "I'll save your cookie on next rerun."

    if st.button("No really, change it now"):
        cookies.save()  # Force saving the cookies now, without a rerun
