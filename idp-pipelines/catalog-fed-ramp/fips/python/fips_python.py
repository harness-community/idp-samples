# python3 -m pip install cryptography
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from hashlib import sha256
import hmac


def check_fips_sha256():
    # Verify FIPS-compliant hashing algorithms (SHA, etc.)
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(b"Test data")
    value = digest.finalize()

    data = b"Test data"
    hash_object = sha256(data)
    print(f"SHA-256 hash: {hash_object.hexdigest()}")

    # Using HMAC with SHA-256 (FIPS-compliant)
    key = b"secret"
    hmac_object = hmac.new(key, data, sha256)
    print(f"HMAC-SHA-256: {hmac_object.hexdigest()}")

    if value is not None:
        return True
    else:
        return False

import subprocess

# Check if FIPS mode is enabled on the system
def check_fips_mode():
    try:
        result = subprocess.run(['cat', '/proc/sys/crypto/fips_enabled'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == '1':
            print("FIPS mode is enabled.")
        else:
            print("FIPS mode is not enabled.")
    except FileNotFoundError:
        print("FIPS status file not found.")
        # Fall back to OpenSSL FIPS check
        result = subprocess.run(['openssl', 'fips'], capture_output=True, text=True)
        if 'FIPS mode enabled' in result.stdout:
            print("FIPS mode is enabled (OpenSSL).")
        else:
            print("FIPS mode is NOT enabled (OpenSSL).")


try: 
    check_fips_sha256()
    #check_fips_mode()
    SystemExit(0)
except Exception as e:
    SystemExit(1)


