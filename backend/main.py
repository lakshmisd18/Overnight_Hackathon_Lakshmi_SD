import os
import json
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3
import requests

# Load .env
load_dotenv()

# -------------------------
# FASTAPI APP
# -------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)

# -------------------------
# BLOCKCHAIN SETUP
# -------------------------
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RAW_CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

# Convert to checksum address (important!)
CONTRACT_ADDRESS = Web3.to_checksum_address(RAW_CONTRACT_ADDRESS)

# Connect to Hardhat local node
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load ABI
with open("blockchain/contract_abi.json") as f:
    ABI = json.load(f)["abi"]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# Wallet
account = w3.eth.account.from_key(PRIVATE_KEY)
WALLET_ADDRESS = account.address


# -------------------------
# IPFS UPLOAD
# -------------------------
def upload_to_ipfs(path):
    files = {"file": open(path, "rb")}
    res = requests.post("https://ipfs.io/api/v0/add", files=files)
    return res.json()["Hash"]


# ===========================================================
# 1️⃣ REGISTER FILE (IPFS + Blockchain)
# ===========================================================
@app.post("/register_ipfs")
async def register_ipfs(
    file: UploadFile = File(...),
    ownerName: str = Form(...),
    ownerEmail: str = Form(...)
):
    # Save file locally
    saved_path = f"uploads/{file.filename}"
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload to IPFS
    cid = upload_to_ipfs(saved_path)

    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)

    tx = contract.functions.registerWork(
        cid,
        ownerName,
        ownerEmail
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 5000000,
        "gasPrice": w3.to_wei("1", "gwei")
    })

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    return {"success": True, "cid": cid, "txHash": tx_hash.hex()}


# ===========================================================
# 2️⃣ VERIFY FILE (upload → IPFS → match CID)
# ===========================================================
@app.post("/verify_ipfs")
async def verify_ipfs(file: UploadFile = File(...)):
    saved_path = f"uploads/{file.filename}"

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cid = upload_to_ipfs(saved_path)

    owner = contract.functions.checkOwner(cid).call()

    return {"cid": cid, "owner": owner}


# ===========================================================
# 3️⃣ RAISE DISPUTE
# ===========================================================
@app.post("/dispute")
async def dispute(
    cid: str = Form(...),
    claimantName: str = Form(...),
    explanation: str = Form(...)
):
    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)

    tx = contract.functions.raiseDispute(
        cid,
        claimantName,
        explanation
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 5000000,
        "gasPrice": w3.to_wei("1", "gwei")
    })

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    return {"success": True, "txHash": tx_hash.hex()}


# ===========================================================
# 4️⃣ GET ALL DISPUTES
# ===========================================================
@app.get("/disputes")
async def list_disputes():
    disputes = contract.functions.getAllDisputes().call()
    return disputes


# ===========================================================
# 5️⃣ RESPOND TO A DISPUTE
# ===========================================================
@app.post("/respond")
async def respond(
    disputeId: int = Form(...),
    response: str = Form(...)
):
    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)

    tx = contract.functions.respondToDispute(
        disputeId,
        response
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 5000000,
        "gasPrice": w3.to_wei("1", "gwei")
    })

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    return {"success": True}


# ===========================================================
# 6️⃣ ADMIN DECISION
# ===========================================================
@app.post("/decision")
async def admin_decision(
    disputeId: int = Form(...),
    decision: str = Form(...)
):
    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)

    tx = contract.functions.adminDecision(
        disputeId,
        decision
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 5000000,
        "gasPrice": w3.to_wei("1", "gwei")
    })

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    return {"success": True}


# ===========================================================
# 7️⃣ BLOCKCHAIN EXPLORER (get all works)
# ===========================================================
@app.get("/blockchain")
async def blockchain_records():
    works = contract.functions.getAllWorks().call()
    return works
