from __future__ import annotations


def id_to_hex(obj) -> str:
    """Convert an object's ID to a shorter hexadecimal representation."""
    return hex(id(obj)).upper()[2:]
