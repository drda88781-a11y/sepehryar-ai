"""
Security module for credential encryption (Windows DPAPI / Machine Keyed)
and sensitive data masking for safe database sample display.
"""
import base64
import ctypes
import os
import re
import sys
from typing import Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.logger import get_logger

logger = get_logger("security")

# Sensitive column name heuristics for automatic masking
SENSITIVE_COLUMN_KEYWORDS = frozenset([
    "password", "pass", "pwd", "secret", "token", "hash",
    "codemelli", "nationalcode", "melicode", "shomarehesab",
    "cardno", "pan", "cvv", "shaba", "iban"
])

# Phone number regex (Iranian mobile/landline pattern)
PHONE_PATTERN = re.compile(r'(\b09\d{2})\d{4}(\d{3}\b)')
MELLI_PATTERN = re.compile(r'\b\d{10}\b')


# Windows DPAPI Implementation via ctypes
class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.c_ulong),
        ("pbData", ctypes.POINTER(ctypes.c_char))
    ]


def _encrypt_dpapi(plaintext: str) -> Optional[str]:
    """Encrypt string using Windows Data Protection API (DPAPI)."""
    if sys.platform != "win32":
        return None
    try:
        data_bytes = plaintext.encode("utf-8")
        blob_in = DATA_BLOB(len(data_bytes), ctypes.cast(ctypes.create_string_buffer(data_bytes), ctypes.POINTER(ctypes.c_char)))
        blob_out = DATA_BLOB()

        crypt32 = ctypes.windll.crypt32
        # CryptProtectData(pDataIn, szDataDescr, pOptionalEntropy, pvReserved, pPromptStruct, dwFlags, pDataOut)
        if crypt32.CryptProtectData(ctypes.byref(blob_in), "SepehryarSecure", None, None, None, 0, ctypes.byref(blob_out)):
            encrypted_bytes = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return "DPAPI:" + base64.b64encode(encrypted_bytes).decode("ascii")
    except Exception as e:
        logger.debug(f"DPAPI encryption unavailable: {e}")
    return None


def _decrypt_dpapi(encrypted_str: str) -> Optional[str]:
    """Decrypt DPAPI-encrypted string."""
    if sys.platform != "win32" or not encrypted_str.startswith("DPAPI:"):
        return None
    try:
        raw_b64 = encrypted_str[6:]
        encrypted_bytes = base64.b64decode(raw_b64)
        blob_in = DATA_BLOB(len(encrypted_bytes), ctypes.cast(ctypes.create_string_buffer(encrypted_bytes), ctypes.POINTER(ctypes.c_char)))
        blob_out = DATA_BLOB()

        crypt32 = ctypes.windll.crypt32
        if crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            decrypted_bytes = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return decrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"DPAPI decryption failed: {e}")
    return None


def _get_fallback_fernet() -> Fernet:
    """Generate deterministic Fernet cipher based on Windows Machine GUID / Username."""
    salt = b"Sepehryar_AI_Engine_Salt_2026_Local"
    machine_seed = os.environ.get("COMPUTERNAME", "SEPEHRYAR_HOST") + os.environ.get("USERNAME", "DEFAULT_USER")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(machine_seed.encode("utf-8")))
    return Fernet(key)


def encrypt_credential(secret: str) -> str:
    """Encrypt a sensitive credential (like SQL Server password)."""
    if not secret:
        return ""
    # 1. Try Windows DPAPI
    dpapi_result = _encrypt_dpapi(secret)
    if dpapi_result:
        return dpapi_result

    # 2. Fallback to machine-keyed Fernet
    fernet = _get_fallback_fernet()
    enc_token = fernet.encrypt(secret.encode("utf-8")).decode("ascii")
    return "FERNET:" + enc_token


def decrypt_credential(encrypted_str: str) -> str:
    """Decrypt a sensitive credential."""
    if not encrypted_str:
        return ""
    if encrypted_str.startswith("DPAPI:"):
        res = _decrypt_dpapi(encrypted_str)
        if res is not None:
            return res
    elif encrypted_str.startswith("FERNET:"):
        token = encrypted_str[7:]
        fernet = _get_fallback_fernet()
        return fernet.decrypt(token.encode("ascii")).decode("utf-8")

    # If legacy plain text was passed, return as is (for backwards compatibility)
    return encrypted_str


def mask_cell_value(col_name: str, value: Any) -> Any:
    """Mask sensitive column data for preview/reporting."""
    if value is None:
        return None
    val_str = str(value).strip()
    if not val_str:
        return value

    col_lower = col_name.lower().replace("_", "")

    # Check sensitive column names
    if any(k in col_lower for k in SENSITIVE_COLUMN_KEYWORDS):
        return "********"

    # Mask Iranian mobile numbers
    if PHONE_PATTERN.search(val_str):
        return PHONE_PATTERN.sub(r'\1****\2', val_str)

    # Mask 10-digit National ID (leave first 3 and last 2)
    if len(val_str) == 10 and val_str.isdigit():
        return f"{val_str[:3]}*****{val_str[-2:]}"

    return value


def mask_sample_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mask sensitive columns across all sampled rows."""
    if not rows:
        return []
    masked_list = []
    for r in rows:
        masked_row = {}
        for col_name, val in r.items():
            masked_row[col_name] = mask_cell_value(col_name, val)
        masked_list.append(masked_row)
    return masked_list
