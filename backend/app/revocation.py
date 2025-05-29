from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from .db import get_session
from .models import Revoked
from .chain import bulletin, w3, acct
from hashlib import sha256
import json
from datetime import datetime
from typing import List

router = APIRouter()

class MerkleTree:
    """Simple Merkle tree implementation for token revocation"""
    
    def __init__(self, leaves: List[str]):
        self.leaves = [sha256(leaf.encode()).digest() for leaf in leaves]
        self.tree = self._build_tree()
    
    def _build_tree(self):
        if not self.leaves:
            return []
        
        tree = [self.leaves]
        level = self.leaves
        
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                combined = sha256(left + right).digest()
                next_level.append(combined)
            tree.append(next_level)
            level = next_level
        
        return tree
    
    @property
    def root(self) -> bytes:
        return self.tree[-1][0] if self.tree else b'\x00' * 32

@router.post("/revoke-token")
async def revoke_token(
    token_hash: str,
    reason: str = "User request",
    session: Session = Depends(get_session)
):
    """Revoke a specific token and update the on-chain Merkle root"""
    
    # Add to revocation list
    revocation = Revoked(
        token_hash=token_hash,
        ts=datetime.utcnow()
    )
    session.add(revocation)
    session.commit()
    
    # Get all revoked tokens
    revoked_tokens = session.query(Revoked).all()
    token_hashes = [r.token_hash for r in revoked_tokens]
    
    # Build Merkle tree
    merkle_tree = MerkleTree(token_hashes)
    new_root = merkle_tree.root
    
    # Update on-chain revocation root
    try:
        tx = bulletin.functions.setRevocationRoot(new_root).build_transaction({
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 80_000,
            "maxFeePerGas": w3.to_wei("40", "gwei"),
            "maxPriorityFeePerGas": w3.to_wei("2", "gwei"),
        })
        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction).hex()
        
        return {
            "revoked": True,
            "token_hash": token_hash,
            "merkle_root": new_root.hex(),
            "tx_hash": tx_hash,
            "total_revoked": len(token_hashes)
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to update on-chain revocation: {str(e)}")

@router.get("/revocation-status/{token_hash}")
async def check_revocation_status(
    token_hash: str,
    session: Session = Depends(get_session)
):
    """Check if a token is revoked"""
    revoked = session.query(Revoked).filter(
        Revoked.token_hash == token_hash
    ).first()
    
    return {
        "token_hash": token_hash,
        "is_revoked": revoked is not None,
        "revoked_at": revoked.ts if revoked else None
    } 