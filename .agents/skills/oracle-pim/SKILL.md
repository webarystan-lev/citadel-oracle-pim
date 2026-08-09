---
name: oracle-pim
description: Antigravity 2.0 Skill for Citadel Oracle PIM management, Convex DB operations, AES-256 Vault encryption, and Streamlit testing.
---

# 🏛️ Citadel Oracle PIM — Antigravity Skill

This skill equips Antigravity 2.0 agents with workflows for:
1. **Convex DB Sync**: Running `npx convex dev` and verifying queries/mutations for `journals`, `projects`, `notes`, `vault`.
2. **Security & Encryption**: Testing AES-256 Fernet encryption with `providers/security.py`.
3. **Multi-Model AI Streaming**: Verifying Google Gemini, Anthropic Claude, and Mistral AI stream handlers.

## Common Operations

### 1. Verify Convex DB Connection
```python
from providers.convex_client import ConvexBridge
bridge = ConvexBridge()
print("Connected:", bridge.check_connection())
```

### 2. Test Vault Encryption
```python
from providers.security import encrypt_secret, decrypt_secret
encrypted = encrypt_secret("my_secret_token", "master_pass")
decrypted = decrypt_secret(encrypted, "master_pass")
assert decrypted == "my_secret_token"
```

### 3. Run Web App
```bash
streamlit run app.py
```
