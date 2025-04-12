import streamlit as st
import subprocess
import json
import os
from PIL import Image

# Set page config with a background image
st.set_page_config(page_title="ZKP Verification", layout="wide")

# Custom CSS for background image and styling
st.markdown(
    """
    <style>
        body {
            background-image: url('https://source.unsplash.com/1600x900/?blockchain,technology');
            background-size: cover;
        }
        .stTextInput, .stButton, .stTextArea {
            border-radius: 10px;
            padding: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Hardcoded login credentials
USERNAME = "admin"
PASSWORD = "zkp123"

# Session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Login Page
if not st.session_state.authenticated:
    st.title("🔐 Login to Access ZKP Verification")
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")
    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Login Successful!")
            st.rerun()
        else:
            st.error("❌ Invalid credentials. Please try again.")
else:
    # Main App - ZKP Verification
    st.title("🔍 Zero-Knowledge Proof (ZKP) Verification")
    
    contract_address = st.text_input("Enter Smart Contract Address:", "")
    if st.button("Verify Contract"):
        if not contract_address:
            st.error("❌ Please enter a valid contract address.")
        else:
            st.info("🔹 Running verification process... Please wait.")
            
            # Run Hardhat command
            command_hardhat = f"cd scripts && CONTRACT_ADDRESS={contract_address} npx hardhat run save2.js --network localhost"
            result_hardhat = subprocess.run(command_hardhat, shell=True, capture_output=True, text=True)
            
            if result_hardhat.returncode == 0:
                st.success("✅ Contract verification successful!")
                
                # Run snarkjs verification
                command_snarkjs = "cd verifyJSON && snarkjs groth16 verify verification_key.json public.json proof.json"
                result_snarkjs = subprocess.run(command_snarkjs, shell=True, capture_output=True, text=True)
                
                if result_snarkjs.returncode == 0:
                    st.success("✅ ZKP Verification Successful!")
                    
                    # Load and display proof.json
                    proof_path = "verifyJSON/proof.json"
                    if os.path.exists(proof_path):
                        with open(proof_path, "r") as f:
                            proof_data = json.load(f)
                        
                    else:
                        st.error("❌ Proof JSON not found!")
                else:
                    st.error("❌ ZKP verification failed!")
                    st.text(result_snarkjs.stderr)
            else:
                st.error("❌ Smart contract verification failed!")
                st.text(result_hardhat.stderr)
    
    # Logout Button
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
