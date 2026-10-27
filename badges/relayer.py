"""Gasless Web3 Relayer Service for SpeakWise Soulbound Badges on Base L2.

Allows verified speakers to claim their soulbound credentials without paying
blockchain gas fees. SpeakWise sponsors the gas fees (<$0.0001 on Base Sepolia)
via an authorized platform relayer account.
"""

import hashlib
import json
import logging
import os
import secrets
import subprocess
import time
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


def generate_simulated_tx_hash(recipient_address: str, token_id: int) -> str:
    """Generate a realistic, deterministic-looking 66-character Base Sepolia transaction hash."""
    seed = (
        f"{recipient_address.lower()}-{token_id}-{time.time()}-{secrets.token_hex(8)}"
    )
    return "0x" + hashlib.sha256(seed.encode("utf-8")).hexdigest()


def award_badge_on_chain(recipient_address: str, token_id: int) -> dict:
    """Execute or simulate an on-chain badge award transaction.

    Args:
        recipient_address: EVM address of recipient
        token_id: ERC-1155 token identifier (1 - 6)

    Returns:
        dict with:
            - tx_hash (str)
            - simulated (bool)
            - network (str)
    """
    clean_recipient = str(recipient_address).strip()
    contract_addr = getattr(
        settings,
        "SPEAKWISE_BADGES_CONTRACT_ADDRESS",
        "",
    ).strip()
    relayer_key = getattr(settings, "BASE_RELAYER_PRIVATE_KEY", "").strip()

    # Locate contracts directory and mint script
    contracts_dir = Path(settings.BASE_DIR).parent.parent / "speakwise-contracts"
    mint_script = contracts_dir / "scripts" / "mintBadge.js"

    if (
        relayer_key
        and not relayer_key.startswith("0x0000000000000")
        and mint_script.exists()
    ):
        try:
            logger.info(
                f"[RELAYER-LIVE] Broadcasting transaction on Base Sepolia for token {token_id} to {clean_recipient}..."
            )
            env = os.environ.copy()
            env["RECIPIENT_ADDRESS"] = clean_recipient
            env["TOKEN_ID"] = str(token_id)
            env["SPEAKWISE_BADGES_CONTRACT_ADDRESS"] = contract_addr
            env["PRIVATE_KEY"] = relayer_key
            env["CI"] = "true"

            proc = subprocess.run(
                [
                    "npx",
                    "hardhat",
                    "run",
                    "scripts/mintBadge.js",
                    "--network",
                    "baseSepolia",
                ],
                cwd=str(contracts_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=45,
            )

            # Search output lines for JSON result
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.startswith("{") and "txHash" in line:
                    data = json.loads(line)
                    tx_hash = data.get("txHash")
                    if tx_hash:
                        logger.info(
                            f"[RELAYER-LIVE] ✅ Confirmed on Base Sepolia: {tx_hash}"
                        )
                        return {
                            "tx_hash": tx_hash,
                            "simulated": False,
                            "network": "base-sepolia",
                        }
                    elif data.get("alreadyHeld"):
                        logger.info(
                            f"[RELAYER-LIVE] Speaker already holds token {token_id} on-chain"
                        )
                        return {
                            "tx_hash": data.get("txHash") or None,
                            "simulated": False,
                            "network": "base-sepolia",
                        }

            logger.warning(
                f"[RELAYER] Hardhat output did not return txHash: {proc.stdout} {proc.stderr}"
            )
        except Exception as e:
            logger.error(
                f"[RELAYER-ERROR] Hardhat runner execution failed: {e}", exc_info=True
            )

    # Fallback simulation
    logger.info(
        f"[RELAYER-FALLBACK] Returning simulated tx hash for token {token_id} to {clean_recipient}"
    )
    simulated_hash = generate_simulated_tx_hash(clean_recipient, token_id)
    return {
        "tx_hash": simulated_hash,
        "simulated": True,
        "network": "base-sepolia",
    }
