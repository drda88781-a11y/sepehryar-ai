"""
Tests for credential encryption, log scrubbing, and sensitive data masking.
"""
from app.core.logger import scrub_credentials
from app.core.security import (
    encrypt_credential,
    decrypt_credential,
    mask_sample_rows,
    mask_cell_value,
)


def test_credential_encryption_and_decryption():
    """Verify passwords are encrypted and reversibly decrypted."""
    plain_password = "SuperSecretPassword123#!"
    encrypted = encrypt_credential(plain_password)
    assert encrypted != plain_password
    assert encrypted.startswith("DPAPI:") or encrypted.startswith("FERNET:")

    decrypted = decrypt_credential(encrypted)
    assert decrypted == plain_password


def test_credentials_not_logged():
    """Verify log scrubber removes passwords and tokens from string payloads."""
    log_sample = "Connecting with PWD=VeryConfidentialPass99; Server=192.168.1.1; User=sa;"
    scrubbed = scrub_credentials(log_sample)
    assert "VeryConfidentialPass99" not in scrubbed
    assert "[PROTECTED]" in scrubbed

    api_token_sample = "Header Authorization: Bearer abc123xyzSecretToken; action=login"
    scrubbed_token = scrub_credentials(api_token_sample)
    assert "abc123xyzSecretToken" not in scrubbed_token
    assert "[PROTECTED]" in scrubbed_token


def test_sensitive_data_masking():
    """Verify national ID and phone numbers are masked."""
    # Phone number
    masked_phone = mask_cell_value("Mobile", "09121234567")
    assert masked_phone == "0912****567"

    # National code column is completely masked
    masked_melli = mask_cell_value("CodeMelli", "0012345678")
    assert masked_melli == "********"

    # Generic column with 10-digit national ID pattern
    masked_doc = mask_cell_value("DocNumber", "0012345678")
    assert masked_doc == "001*****78"

    # Password column
    masked_pass = mask_cell_value("Password", "SecretPass")
    assert masked_pass == "********"
