"""
The Forge — Cryptography Core
AES-256-GCM, XOR chains, RC4, key derivation, payload encoding.
"""

import os
import base64
import hashlib
import hmac
import struct
import secrets
import string
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Key Derivation
# ---------------------------------------------------------------------------

def derive_key(password: str, salt: Optional[bytes] = None, iterations: int = 100_000, key_len: int = 32) -> Tuple[bytes, bytes]:
    """PBKDF2-HMAC-SHA256 key derivation."""
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations, dklen=key_len)
    return key, salt


def generate_key(length: int = 32) -> bytes:
    """Generate a cryptographically secure random key."""
    return secrets.token_bytes(length)


def generate_passphrase(word_count: int = 6) -> str:
    """Generate a random passphrase from printable characters."""
    charset = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(charset) for _ in range(word_count * 4))


# ---------------------------------------------------------------------------
# AES-256-GCM (via PyCryptodome or fallback XOR)
# ---------------------------------------------------------------------------

def aes_encrypt(plaintext: bytes, key: bytes) -> bytes:
    """
    AES-256-GCM encryption.
    Returns: nonce (12) + tag (16) + ciphertext
    Falls back to XOR if PyCryptodome is not installed.
    """
    try:
        from Crypto.Cipher import AES
        nonce = os.urandom(12)
        cipher = AES.new(key[:32], AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        return nonce + tag + ciphertext
    except ImportError:
        # Fallback: XOR with key-derived stream (not production-grade)
        return _xor_fallback_encrypt(plaintext, key)


def aes_decrypt(data: bytes, key: bytes) -> bytes:
    """
    AES-256-GCM decryption.
    Expects: nonce (12) + tag (16) + ciphertext
    """
    try:
        from Crypto.Cipher import AES
        nonce = data[:12]
        tag = data[12:28]
        ciphertext = data[28:]
        cipher = AES.new(key[:32], AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)
    except ImportError:
        return _xor_fallback_decrypt(data, key)


def _xor_fallback_encrypt(plaintext: bytes, key: bytes) -> bytes:
    """XOR fallback with marker prefix."""
    marker = b"\xDE\xAD"  # identify fallback mode
    stream = _expand_key(key, len(plaintext))
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, stream))
    return marker + ciphertext


def _xor_fallback_decrypt(data: bytes, key: bytes) -> bytes:
    """XOR fallback decryption."""
    if data[:2] == b"\xDE\xAD":
        ciphertext = data[2:]
        stream = _expand_key(key, len(ciphertext))
        return bytes(a ^ b for a, b in zip(ciphertext, stream))
    raise ValueError("Unknown encryption format")


# ---------------------------------------------------------------------------
# XOR Operations
# ---------------------------------------------------------------------------

def xor_encode(data: bytes, key: bytes) -> bytes:
    """Simple XOR encode with repeating key."""
    key_len = len(key)
    return bytes(data[i] ^ key[i % key_len] for i in range(len(data)))


def xor_decode(data: bytes, key: bytes) -> bytes:
    """XOR decode (same as encode — symmetric)."""
    return xor_encode(data, key)


def multi_xor(data: bytes, keys: list[bytes]) -> bytes:
    """Chain multiple XOR keys for layered encoding."""
    result = data
    for key in keys:
        result = xor_encode(result, key)
    return result


def _expand_key(key: bytes, length: int) -> bytes:
    """Expand key to target length using SHA-256 chaining."""
    expanded = b""
    counter = 0
    while len(expanded) < length:
        expanded += hashlib.sha256(key + struct.pack("<I", counter)).digest()
        counter += 1
    return expanded[:length]


# ---------------------------------------------------------------------------
# RC4 Stream Cipher
# ---------------------------------------------------------------------------

def rc4(data: bytes, key: bytes) -> bytes:
    """RC4 stream cipher — encrypt and decrypt are the same operation."""
    S = list(range(256))
    j = 0
    # KSA
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    # PRGA
    i = j = 0
    output = bytearray()
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        output.append(byte ^ S[(S[i] + S[j]) % 256])
    return bytes(output)


# ---------------------------------------------------------------------------
# Encoding Utilities
# ---------------------------------------------------------------------------

def b64_encode(data: bytes) -> str:
    """Standard Base64 encoding."""
    return base64.b64encode(data).decode()


def b64_decode(data: str) -> bytes:
    """Standard Base64 decoding."""
    return base64.b64decode(data)


def b64_url_encode(data: bytes) -> str:
    """URL-safe Base64 (no padding)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64_url_decode(data: str) -> bytes:
    """URL-safe Base64 decode with padding restoration."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def hex_encode(data: bytes) -> str:
    """Hex encoding."""
    return data.hex()


def hex_decode(data: str) -> bytes:
    """Hex decoding."""
    return bytes.fromhex(data)


# ---------------------------------------------------------------------------
# Payload Obfuscation
# ---------------------------------------------------------------------------

def uuid_encode(shellcode: bytes) -> list[str]:
    """
    Encode shellcode as a list of UUIDs.
    Pads to 16-byte boundary. Used for UUID-based shellcode injection.
    """
    import uuid
    # Pad to 16-byte alignment
    padding = 16 - (len(shellcode) % 16)
    if padding != 16:
        shellcode += b"\x90" * padding  # NOP sled padding
    uuids = []
    for i in range(0, len(shellcode), 16):
        chunk = shellcode[i:i + 16]
        uuids.append(str(uuid.UUID(bytes_le=chunk)))
    return uuids


def ipv4_encode(shellcode: bytes) -> list[str]:
    """Encode shellcode as fake IPv4 addresses (4 bytes each)."""
    padding = 4 - (len(shellcode) % 4)
    if padding != 4:
        shellcode += b"\x90" * padding
    addresses = []
    for i in range(0, len(shellcode), 4):
        chunk = shellcode[i:i + 4]
        addresses.append(".".join(str(b) for b in chunk))
    return addresses


def mac_encode(shellcode: bytes) -> list[str]:
    """Encode shellcode as fake MAC addresses (6 bytes each)."""
    padding = 6 - (len(shellcode) % 6)
    if padding != 6:
        shellcode += b"\x90" * padding
    macs = []
    for i in range(0, len(shellcode), 6):
        chunk = shellcode[i:i + 6]
        macs.append(":".join(f"{b:02X}" for b in chunk))
    return macs


def string_obfuscate(code: str, var_name: str = "s") -> str:
    """
    Obfuscate a string by converting to chr() concatenation.
    Example: "hello" → chr(104)+chr(101)+chr(108)+chr(108)+chr(111)
    """
    chars = "+".join(f"chr({ord(c)})" for c in code)
    return f"{var_name}={chars}"


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha512(data: bytes) -> str:
    return hashlib.sha512(data).hexdigest()


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def hmac_sha256(data: bytes, key: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


def verify_hmac(data: bytes, key: bytes, expected: bytes) -> bool:
    computed = hmac_sha256(data, key)
    return hmac.compare_digest(computed, expected)


# ---------------------------------------------------------------------------
# Quick API
# ---------------------------------------------------------------------------

def encrypt(plaintext: bytes, password: str) -> bytes:
    """High-level encrypt: derive key from password → AES-256-GCM."""
    key, salt = derive_key(password)
    encrypted = aes_encrypt(plaintext, key)
    return salt + encrypted  # salt (16) + nonce (12) + tag (16) + ciphertext


def decrypt(data: bytes, password: str) -> bytes:
    """High-level decrypt: extract salt → derive key → AES-256-GCM."""
    salt = data[:16]
    encrypted = data[16:]
    key, _ = derive_key(password, salt=salt)
    return aes_decrypt(encrypted, key)
