import streamlit as st
from modules.hue_controller import HueControlApp

st.sidebar.subheader("Philips Hue Control")
st.sidebar.write("by python")
st.sidebar.markdown("***")

if not "app" in st.session_state:
    st.session_state.app = HueControlApp()
app = st.session_state.app

if not app.hue:
    app.get_hue()

if app.hue:
    st.sidebar.write(f"Hi, {app.user.name}")
    st.sidebar.text("")
    lights = app.hue.get_lights()

    color = st.sidebar.color_picker('Color', value='#ffffff')
    brightness = st.sidebar.slider('Brightness', min_value=1, max_value=255, value=255, step=1)

    for l in lights:
        l.on()
        l.set_color(hexa=color)
        l.set_brightness(brightness)

    if st.sidebar.button('OFF'):
        for l in lights:
            l.off()
