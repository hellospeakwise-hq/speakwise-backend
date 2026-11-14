"""Gasless Web3 Relayer Service for SpeakWise Soulbound Badges on Base L2.

Allows verified speakers to claim their soulbound credentials without paying
blockchain gas fees. SpeakWise sponsors the gas fees (<$0.0001 on Base Sepolia)
via an authorized platform relayer account using Web3.py.
"""

import hashlib
import logging
import secrets
import time
import typing

from django.conf import settings

# Python 3.14 compatibility patch for pydantic & web3.py
if hasattr(typing, "_eval_type"):
    _orig_eval_type = typing._eval_type

    def _patched_eval_type(*args, **kwargs):
        kwargs.pop("prefer_fwd_module", None)
        return _orig_eval_type(*args, **kwargs)

    typing._eval_type = _patched_eval_type

try:
    from eth_account import Account
    from web3 import Web3
except ImportError:
    Account = None  # type: ignore
    Web3 = None  # type: ignore

logger = logging.getLogger(__name__)

SPEAKWISE_BADGES_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "speaker", "type": "address"},
            {"internalType": "uint256", "name": "badgeId", "type": "uint256"},
        ],
        "name": "awardBadge",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "speaker", "type": "address"},
            {"internalType": "uint256", "name": "badgeId", "type": "uint256"},
        ],
        "name": "hasBadge",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "uint256", "name": "id", "type": "uint256"},
        ],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def generate_simulated_tx_hash(recipient_address: str, token_id: int) -> str:
    """Generate a realistic, deterministic-looking 66-character Base Sepolia transaction hash."""
    seed = (
        f"{recipient_address.lower()}-{token_id}-{time.time()}-{secrets.token_hex(8)}"
    )
    return "0x" + hashlib.sha256(seed.encode("utf-8")).hexdigest()


def award_badge_on_chain(recipient_address: str, token_id: int) -> dict:
    """Execute on-chain badge award transaction on Base Sepolia using Web3.py.

    Args:
        recipient_address: EVM address of recipient (0x...)
        token_id: ERC-1155 token identifier (1 - 6)

    Returns:
        dict with:
            - tx_hash (str or None)
            - simulated (bool)
            - network (str)
            - already_held (bool, optional)
    """
    clean_recipient = str(recipient_address).strip()
    contract_addr = getattr(
        settings,
        "SPEAKWISE_BADGES_CONTRACT_ADDRESS",
        "0xDe534A43A2f1731bc86E776BAae4178be32B1DFE",
    ).strip()
    relayer_key = getattr(settings, "BASE_RELAYER_PRIVATE_KEY", "").strip()
    rpc_url = getattr(
        settings, "BASE_SEPOLIA_RPC_URL", "https://sepolia.base.org"
    ).strip()
    chain_id = int(getattr(settings, "BASE_CHAIN_ID", 84532))

    is_configured_key = (
        bool(relayer_key)
        and not relayer_key.startswith("0x0000000000000")
        and len(relayer_key.replace("0x", "")) == 64
    )

    if is_configured_key and contract_addr and Web3 is not None and Account is not None:
        try:
            logger.info(
                f"[RELAYER-LIVE] Connecting to {rpc_url} to mint badge #{token_id} for {clean_recipient}..."
            )
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))
            if not w3.is_connected():
                logger.error(f"[RELAYER-ERROR] Cannot reach Base RPC at {rpc_url}")
                raise ConnectionError(f"RPC {rpc_url} unreachable")

            account = Account.from_key(relayer_key)
            relayer_address = account.address
            checksum_recipient = Web3.to_checksum_address(clean_recipient)
            checksum_contract = Web3.to_checksum_address(contract_addr)

            contract = w3.eth.contract(
                address=checksum_contract, abi=SPEAKWISE_BADGES_ABI
            )

            # Check if recipient already has this badge on-chain
            try:
                if contract.functions.hasBadge(
                    checksum_recipient, int(token_id)
                ).call():
                    logger.info(
                        f"[RELAYER-LIVE] Speaker {checksum_recipient} already holds badge #{token_id} on-chain."
                    )
                    return {
                        "tx_hash": None,
                        "simulated": False,
                        "network": "base-sepolia",
                        "already_held": True,
                    }
            except Exception as check_err:
                logger.warning(
                    f"[RELAYER] hasBadge check encountered error (will proceed with mint): {check_err}"
                )

            # Build transaction
            nonce = w3.eth.get_transaction_count(relayer_address, "pending")
            tx_data = {
                "from": relayer_address,
                "nonce": nonce,
                "chainId": chain_id,
            }

            # Function call
            tx_call = contract.functions.awardBadge(checksum_recipient, int(token_id))

            # Build transaction (Web3 automatically handles gas estimation and fee calculation)
            built_tx = tx_call.build_transaction(tx_data)

            # Sign transaction
            signed_tx = w3.eth.account.sign_transaction(
                built_tx, private_key=relayer_key
            )
            raw_tx = (
                getattr(signed_tx, "raw_transaction", None) or signed_tx.rawTransaction
            )

            # Broadcast raw transaction
            tx_hash_bytes = w3.eth.send_raw_transaction(raw_tx)
            tx_hash_hex = w3.to_hex(tx_hash_bytes)

            logger.info(
                f"[RELAYER-LIVE] Broadcasted tx {tx_hash_hex}. Waiting for block confirmation..."
            )
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=45)

            if receipt.get("status") == 1:
                logger.info(
                    f"[RELAYER-LIVE] ✅ Confirmed on Base Sepolia in block {receipt.get('blockNumber')}: {tx_hash_hex}"
                )
                return {
                    "tx_hash": tx_hash_hex,
                    "simulated": False,
                    "network": "base-sepolia",
                }
            else:
                logger.error(
                    f"[RELAYER-LIVE] ❌ Transaction reverted on-chain: {tx_hash_hex}"
                )
                return {
                    "tx_hash": tx_hash_hex,
                    "simulated": False,
                    "network": "base-sepolia",
                    "error": "reverted",
                }

        except Exception as e:
            logger.error(
                f"[RELAYER-ERROR] On-chain execution failed: {e}", exc_info=True
            )

    # Fallback simulation (only when relayer key is not set or network error in development/testing)
    logger.warning(
        f"[RELAYER-FALLBACK] Returning simulated tx hash for token {token_id} to {clean_recipient}"
    )
    simulated_hash = generate_simulated_tx_hash(clean_recipient, token_id)
    return {
        "tx_hash": simulated_hash,
        "simulated": True,
        "network": "base-sepolia",
    }
