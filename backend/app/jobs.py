# app/revocation.py   (or wherever you keep the jobs)

from hashlib import sha256
from typing import List

from .db       import DBSession
from .models   import Revoked
from .chain    import bulletin, acct, w3


# ──────────────────────────────
# Tiny Merkle helper (≈10 lines)
# ──────────────────────────────
def _merkle_root(leaves: List[bytes]) -> bytes:
    """
    Computes a Bitcoin-style Merkle root (duplicating the odd last leaf at
    every level).  Returns raw 32-byte hash so it can be sent straight to
    a bytes32 Solidity parameter.
    """
    if not leaves:
        return b"\0" * 32                    # empty tree sentinel

    level = [sha256(x).digest() for x in leaves]

    while len(level) > 1:
        if len(level) & 1:                   # odd → duplicate last
            level.append(level[-1])
        level = [
            sha256(level[i] + level[i + 1]).digest()
            for i in range(0, len(level), 2)
        ]
    return level[0]


# ─────────────────────────────────────────────
# Job that pushes the root to the Bulletin SC
# ─────────────────────────────────────────────
def update_revocation_root() -> None:
    with DBSession() as session:
        # Revoked.token_hash is already a *hex* SHA-256 digest
        leaves = [bytes.fromhex(r.token_hash) for r in session.query(Revoked).all()]

    if not leaves:
        return                                # nothing to revoke yet

    root = _merkle_root(sorted(leaves))       # sorted == deterministic tree

    tx = bulletin.functions.setRevocationRoot(root).build_transaction(
        {
            "from":  acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas":   80_000,
        }
    )
    signed = acct.sign_transaction(tx)
    w3.eth.send_raw_transaction(signed.rawTransaction)
# app/revocation.py   (or wherever you keep the jobs)

from hashlib import sha256
from typing import List

from .db       import DBSession
from .models   import Revoked
from .chain    import bulletin, acct, w3


# ──────────────────────────────
# Tiny Merkle helper (≈10 lines)
# ──────────────────────────────
def _merkle_root(leaves: List[bytes]) -> bytes:
    """
    Computes a Bitcoin-style Merkle root (duplicating the odd last leaf at
    every level).  Returns raw 32-byte hash so it can be sent straight to
    a bytes32 Solidity parameter.
    """
    if not leaves:
        return b"\0" * 32                    # empty tree sentinel

    level = [sha256(x).digest() for x in leaves]

    while len(level) > 1:
        if len(level) & 1:                   # odd → duplicate last
            level.append(level[-1])
        level = [
            sha256(level[i] + level[i + 1]).digest()
            for i in range(0, len(level), 2)
        ]
    return level[0]


# ─────────────────────────────────────────────
# Job that pushes the root to the Bulletin SC
# ─────────────────────────────────────────────
def update_revocation_root() -> None:
    with DBSession() as session:
        # Revoked.token_hash is already a *hex* SHA-256 digest
        leaves = [bytes.fromhex(r.token_hash) for r in session.query(Revoked).all()]

    if not leaves:
        return                                # nothing to revoke yet

    root = _merkle_root(sorted(leaves))       # sorted == deterministic tree

    tx = bulletin.functions.setRevocationRoot(root).build_transaction(
        {
            "from":  acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas":   80_000,
        }
    )
    signed = acct.sign_transaction(tx)
    w3.eth.send_raw_transaction(signed.rawTransaction)
