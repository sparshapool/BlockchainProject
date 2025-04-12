import streamlit as st
import requests
from PIL import Image
import numpy as np
import hashlib
import io
import pytesseract
import re

# Pinata API credentials (Keep them safe in real applications!)
PINATA_API_KEY = "e2295aa18c3c3b11dc08"     #You can change this by making your own pinata account 
PINATA_SECRET_API_KEY = "63942f23ce2760b6f0c0bced7f71a547e702be34017abf8954bdb02f4f015f9c"

# Dummy auth
def login(username, password):
    return username == "admin" and password == "password"

# Fetch files from Pinata
def get_pinned_files():
    url = "https://api.pinata.cloud/data/pinList"
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_API_KEY
    }
    params = {
        "status": "pinned",
        "pageLimit": 20,
        "pageOffset": 0
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("rows", [])
        else:
            st.error(f"❌ Error fetching data: {response.text}")
            return []
    except Exception as e:
        st.error(f"❌ Exception: {e}")
        return []

# XOR decryption using key derived from contract address
def decrypt_image_with_contract(encrypted_bytes: bytes, contract_address: str) -> Image.Image:
    image = Image.open(io.BytesIO(encrypted_bytes)).convert("RGB")
    encrypted_array = np.array(image)

    hash_seed = hashlib.sha256(contract_address.encode('utf-8')).digest()
    key_stream = np.frombuffer(hash_seed * ((encrypted_array.size // len(hash_seed)) + 1), dtype=np.uint8)
    key_stream = key_stream[:encrypted_array.size].reshape(encrypted_array.shape)

    decrypted_array = np.bitwise_xor(encrypted_array, key_stream)
    decrypted_image = Image.fromarray(decrypted_array.astype(np.uint8))
    return decrypted_image

# OCR-based validation for PAN card
def extract_pan_details(image: Image.Image):
    text = pytesseract.image_to_string(image, config="--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/")
    pan_number = re.findall(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
    dob = re.findall(r"\d{2}/\d{2}/\d{4}", text)
    return pan_number[0] if pan_number else None, dob[0] if dob else None

# Streamlit UI
st.set_page_config(page_title="🔐 IPFS PAN Decryption Portal")
st.title("🔐 Law Enforcement IPFS Access Portal")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")
        if login_btn:
            if login(username, password):
                st.session_state.authenticated = True
                st.success("✅ Login successful")
            else:
                st.error("❌ Invalid credentials")

# Main App
else:
    st.sidebar.success("Logged in as admin")
    st.header("🧾 Decrypt & Verify PAN Card via IPFS")

    contract_address = st.text_input("Enter Contract Address for Decryption")

    if contract_address:
        pinned_files = get_pinned_files()
        match_found = False

        for file in pinned_files:
            name = file.get("metadata", {}).get("name", "Unnamed File")
            ipfs_hash = file.get("ipfs_pin_hash", "")
            ipfs_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"

            try:
                response = requests.get(ipfs_url)
                if response.status_code == 200:
                    decrypted_image = decrypt_image_with_contract(response.content, contract_address)
                    pan_number, dob = extract_pan_details(decrypted_image)

                    if pan_number and dob:
                        st.subheader(f"✅ Match Found: {name}")
                        st.image(decrypted_image, caption=f"Decrypted from CID: {ipfs_hash}", use_container_width=True)
                        st.write(f"**Extracted PAN Number:** {pan_number}")
                        st.write(f"**Extracted DOB:** {dob}")
                        match_found = True
                        break

            except Exception as e:
                st.warning(f"❌ Failed to process {name}: {e}")
                continue

        if not match_found:
            st.warning("⚠️ No valid PAN card matched with the given contract address.")
