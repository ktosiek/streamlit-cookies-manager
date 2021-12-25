# Streamlit Cookies Manager

Access and change browser cookies from Streamlit scripts:
```python
import streamlit as st
from streamlit_cookies_manager import CookieManager

# This should be on top of your script
cookies = CookieManager()
if not cookies.ready():
    # Wait for the component to load and send us current cookies.
    st.stop()

st.write("Current cookies:", cookies)
value = st.text_input("New value for a cookie")
if st.button("Change the cookie"):
    cookies['a-cookie'] = value  # This will get saved on next rerun
    if st.button("No really, change it now"):
        cookies.save()  # Force saving the cookies now, without a rerun
```
