from eth_account import Account

# Generate a new Ethereum account
acct = Account.create()

print("🔐 Wallet created:")
print(f"Address:     {acct.address}")
print(f"Private Key: {acct.key.hex()}")

# Save to .env-compatible format
with open(".env.wallet", "w") as f:
    f.write(f"PRIVATE_KEY={acct.key.hex()}\n")
