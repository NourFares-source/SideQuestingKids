import streamlit as st

st.set_page_config(page_title="SideQuest AI", layout="centered")
st.title("⚔️ SideQuest AI for Kids")
st.info("Testing Dashboard Connected to FastAPI Backend")

st.write("Welcome to the SideQuest testing interface!")
img = st.camera_input("Take a photo of your quest completion")

if img:
    st.image(img)
    st.success("Photo captured! Ready for backend submission.")