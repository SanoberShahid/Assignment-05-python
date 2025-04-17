import streamlit as st
import hashlib
import json
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode
from datetime import datetime

DATA_FILE = "data.json"
USERS_FILE = "users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def generate_cipher(passkey):
    salt = b'streamlit-salt'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = urlsafe_b64encode(kdf.derive(passkey.encode()))
    return Fernet(key)

stored_data = load_data()
users_data = load_users()

if "stored_data" not in st.session_state:
    st.session_state.stored_data = stored_data
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "page" not in st.session_state:
    st.session_state.page = "Login"

def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

def encrypt_data(text, passkey):
    cipher = generate_cipher(passkey)
    return cipher.encrypt(text.encode()).decode()

def decrypt_data(encrypted_text, passkey):
    try:
        cipher = generate_cipher(passkey)
        return cipher.decrypt(encrypted_text.encode()).decode()
    except:
        return None

st.set_page_config(page_title="Secure Data Vault", page_icon="🛡️", initial_sidebar_state="collapsed")
st.title("🛡️Secure Data Encryption System")
st.caption("Developed by Sanober Shahid")

if not st.session_state.is_logged_in:
    auth_tab = st.radio("Login or Register", ["Login", "Register"], horizontal=True)

    if auth_tab == "Login":
        st.subheader("🔐 Login to Your Vault")
        user_login = st.text_input("👤 Username")

        if st.button("🔓 Login"):
            if user_login in users_data:
                st.session_state.is_logged_in = True
                st.session_state.current_user = user_login
                st.success(f"✅ Welcome, {user_login}!")
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("❌ Incorrect username.")

    elif auth_tab == "Register":
        st.subheader("💊 Create New Account")
        new_user = st.text_input("👤 Username")

        if st.button("📝 Register"):
            if new_user in users_data:
                st.error("❌ Username already exists.")
            elif new_user:
                users_data[new_user] = "default"
                save_users(users_data)
                st.success("✅ Registered successfully! You can now login.")
                st.session_state.page = "home"
                st.rerun()
            else:
                st.warning("⚠️ Please enter a username.")
    st.stop()

menu = ["Home", "Store Data", "Retrieve Data"]
choice = st.sidebar.selectbox("Navigate", menu)

if choice == "Home":
    st.subheader("🏠 Welcome to Your Secure Vault")
    st.markdown("Use the sidebar to store or retrieve your encrypted data.")

elif choice == "Store Data":
    st.subheader("📂 Store Encrypted Data")
    username = st.session_state.current_user
    title = st.text_input("🗂️ Title for Your Secret")
    user_data = st.text_area("📝 Enter Secret Data:")
    passkey = "passkey"  # Dummy passkey used to encrypt/decrypt

    if st.button("🔐 Encrypt & Save"):
        if user_data and title:
            encrypted = encrypt_data(user_data, passkey)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if username not in st.session_state.stored_data:
                st.session_state.stored_data[username] = {}
            st.session_state.stored_data[username][title] = {
                "encrypted": encrypted,
                "passkey": hash_passkey(passkey),
                "timestamp": timestamp
            }
            save_data(st.session_state.stored_data)
            st.success("✅ Data encrypted and saved!")
            with st.expander("📆 Encrypted Text (click to view)"):
                st.code(encrypted, language="text")
            st.text(f"Timestamp: {timestamp}")
        else:
            st.error("⚠️ All fields are required!")

elif choice == "Retrieve Data":
    st.subheader("🔍 Retrieve Your Data")
    username = st.session_state.current_user
    user_entries = st.session_state.stored_data.get(username, {})

    if user_entries:
        selected_title = st.selectbox("📁 Select a Title to Decrypt", list(user_entries.keys()))
        passkey_input = "passkey"  # Fixed dummy passkey

        if st.button("🤩 Decrypt"):
            entry = user_entries.get(selected_title)
            if entry and entry["passkey"] == hash_passkey(passkey_input):
                decrypted = decrypt_data(entry["encrypted"], passkey_input)
                if decrypted:
                    st.success("✅ Decrypted Data:")
                    st.code(decrypted, language="text")
                else:
                    st.error("❌ Failed to decrypt.")
            else:
                st.error("❌ Incorrect passkey.")
    else:
        st.info("ℹ️ You have no saved data yet.")
