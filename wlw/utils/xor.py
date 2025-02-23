"""
Xor related functions.
"""
def obfuscate(key: bytes, data: bytes) -> bytes:
    """
    (de)Obfuscate data using XOR with the obfuscation key.

    Mainly used to discourage editing/save-scumming by making the reverse process
    more annoying, though not impossible.

    As long as the data hasn't been modified, should reverse any obfuscated bytes and vice-versa.

    Args:
    data (bytes): Data to (de)obfuscate.

    Returns:
    bytes: (de)Obfuscated data.
    """
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
