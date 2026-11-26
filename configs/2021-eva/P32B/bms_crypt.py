#!/usr/bin/env python3
"""
bms_crypt.py — decrypt / encrypt LiBAL s-BMS ".bms" configuration files.

A .bms file is just the configuration XML encrypted with AES-128-CBC using a
fixed key and IV compiled into the Lithium Balance Diagnostic Software
(verified against "Diagnostic Software 6.18.0 FREE.exe", a .NET assembly).

    key = b"extremelysecret!"      iv = b"almostassecret!!"
    AES-128-CBC, PKCS#7 padding, plaintext is UTF-8 XML with CRLF and no BOM.

Encrypt is the exact inverse of decrypt: re-encrypting an untouched decrypted
file reproduces the original .bms byte for byte (checked by `selftest`).

Usage
-----
    python3 bms_crypt.py decrypt config2.bms                 # -> config2.xml
    python3 bms_crypt.py decrypt config2.bms -o out.xml
    python3 bms_crypt.py decrypt config2.bms --utf16         # like the tool's own XML export
    python3 bms_crypt.py encrypt edited.xml -o edited.bms
    python3 bms_crypt.py info  *.bms                         # identify / fingerprint
    python3 bms_crypt.py selftest config2.bms                # prove round-trip is exact

`encrypt` verifies its own output by decrypting it again before writing, so a
file that would not load in the Diagnostic Software is never produced.

No third-party dependencies. Uses macOS CommonCrypto when present, otherwise a
built-in AES implementation, so it runs anywhere Python 3 does.
"""

# from __future__ import annotations

import argparse
import hashlib
import os
import sys

KEY = b"extremelysecret!"
IV = b"almostassecret!!"
BLOCK = 16


# --------------------------------------------------------------------------
# AES-128 (pure Python fallback)
# --------------------------------------------------------------------------

_SBOX = bytes.fromhex(
    "637c777bf26b6fc53001672bfed7ab76" "ca82c97dfa5947f0add4a2af9ca472c0"
    "b7fd9326363ff7cc34a5e5f171d83115" "04c723c31896059a071280e2eb27b275"
    "09832c1a1b6e5aa0523bd6b329e32f84" "53d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa8" "51a3408f929d38f5bcb6da2110fff3d2"
    "cd0c13ec5f974417c4a77e3d645d1973" "60814fdc222a908846eeb814de5e0bdb"
    "e0323a0a4906245cc2d3ac629195e479" "e7c8376d8dd54ea96c56f4ea657aae08"
    "ba78252e1ca6b4c6e8dd741f4bbd8b8a" "703eb5664803f60e613557b986c11d9e"
    "e1f8981169d98e949b1e87e9ce5528df" "8ca1890dbfe6426841992d0fb054bb16"
)
_INV_SBOX = bytearray(256)
for _i, _v in enumerate(_SBOX):
    _INV_SBOX[_v] = _i
_INV_SBOX = bytes(_INV_SBOX)
_RCON = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)


def _xt(a: int) -> int:
    a <<= 1
    return (a ^ 0x11B) & 0xFF if a & 0x100 else a


def _mul(a: int, b: int) -> int:
    p = 0
    while b:
        if b & 1:
            p ^= a
        a = _xt(a)
        b >>= 1
    return p


def _expand_key(key: bytes) -> list[bytes]:
    """AES-128 key schedule -> 11 round keys of 16 bytes (column-major)."""
    w = [list(key[i * 4:i * 4 + 4]) for i in range(4)]
    for i in range(4, 44):
        t = list(w[i - 1])
        if i % 4 == 0:
            t = t[1:] + t[:1]
            t = [_SBOX[b] for b in t]
            t[0] ^= _RCON[i // 4 - 1]
        w.append([w[i - 4][j] ^ t[j] for j in range(4)])
    return [bytes(b for word in w[r * 4:r * 4 + 4] for b in word) for r in range(11)]


def _encrypt_block(blk: bytes, rk: list[bytes]) -> bytes:
    s = bytearray(x ^ y for x, y in zip(blk, rk[0]))
    for rnd in range(1, 11):
        s = bytearray(_SBOX[b] for b in s)
        s = bytearray(s[(r + 4 * ((c + r) % 4))] for c in range(4) for r in range(4))
        if rnd != 10:
            t = bytearray(16)
            for c in range(4):
                a0, a1, a2, a3 = s[4 * c:4 * c + 4]
                t[4 * c + 0] = _xt(a0) ^ (_xt(a1) ^ a1) ^ a2 ^ a3
                t[4 * c + 1] = a0 ^ _xt(a1) ^ (_xt(a2) ^ a2) ^ a3
                t[4 * c + 2] = a0 ^ a1 ^ _xt(a2) ^ (_xt(a3) ^ a3)
                t[4 * c + 3] = (_xt(a0) ^ a0) ^ a1 ^ a2 ^ _xt(a3)
            s = t
        s = bytearray(x ^ y for x, y in zip(s, rk[rnd]))
    return bytes(s)


def _decrypt_block(blk: bytes, rk: list[bytes]) -> bytes:
    s = bytearray(x ^ y for x, y in zip(blk, rk[10]))
    for rnd in range(9, -1, -1):
        s = bytearray(s[(r + 4 * ((c - r) % 4))] for c in range(4) for r in range(4))
        s = bytearray(_INV_SBOX[b] for b in s)
        s = bytearray(x ^ y for x, y in zip(s, rk[rnd]))
        if rnd != 0:
            t = bytearray(16)
            for c in range(4):
                a0, a1, a2, a3 = s[4 * c:4 * c + 4]
                t[4 * c + 0] = _mul(a0, 14) ^ _mul(a1, 11) ^ _mul(a2, 13) ^ _mul(a3, 9)
                t[4 * c + 1] = _mul(a0, 9) ^ _mul(a1, 14) ^ _mul(a2, 11) ^ _mul(a3, 13)
                t[4 * c + 2] = _mul(a0, 13) ^ _mul(a1, 9) ^ _mul(a2, 14) ^ _mul(a3, 11)
                t[4 * c + 3] = _mul(a0, 11) ^ _mul(a1, 13) ^ _mul(a2, 9) ^ _mul(a3, 14)
            s = t
    return bytes(s)


def _cbc_py(data: bytes, key: bytes, iv: bytes, encrypt: bool) -> bytes:
    rk = _expand_key(key)
    out = bytearray()
    prev = iv
    for i in range(0, len(data), BLOCK):
        blk = data[i:i + BLOCK]
        if encrypt:
            ct = _encrypt_block(bytes(x ^ y for x, y in zip(blk, prev)), rk)
            out += ct
            prev = ct
        else:
            out += bytes(x ^ y for x, y in zip(_decrypt_block(blk, rk), prev))
            prev = blk
    return bytes(out)


# --------------------------------------------------------------------------
# CommonCrypto fast path (macOS) with automatic fallback
# --------------------------------------------------------------------------

def _cbc_commoncrypto(data: bytes, key: bytes, iv: bytes, encrypt: bool):
    try:
        import ctypes
        lib = ctypes.CDLL("/usr/lib/system/libcommonCrypto.dylib")
    except OSError:
        return None
    import ctypes
    fn = lib.CCCrypt
    fn.argtypes = [ctypes.c_uint32] * 3 + [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    fn.restype = ctypes.c_int32
    out = ctypes.create_string_buffer(len(data) + 32)
    moved = ctypes.c_size_t()
    rc = fn(0 if encrypt else 1, 0, 0, key, len(key), iv, data, len(data),
            out, len(data) + 32, ctypes.byref(moved))
    return out.raw[:moved.value] if rc == 0 else None


def aes_cbc(data: bytes, encrypt: bool, key: bytes = KEY, iv: bytes = IV) -> bytes:
    if len(data) % BLOCK:
        raise ValueError(f"data length {len(data)} is not a multiple of {BLOCK}")
    fast = _cbc_commoncrypto(data, key, iv, encrypt)
    return fast if fast is not None else _cbc_py(data, key, iv, encrypt)


# --------------------------------------------------------------------------
# PKCS#7
# --------------------------------------------------------------------------

def pkcs7_pad(data: bytes) -> bytes:
    n = BLOCK - (len(data) % BLOCK)
    return data + bytes([n]) * n


def pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError("empty plaintext")
    n = data[-1]
    if not 1 <= n <= BLOCK or data[-n:] != bytes([n]) * n:
        raise ValueError("bad PKCS#7 padding — wrong key, or not a .bms file")
    return data[:-n]


# --------------------------------------------------------------------------
# File level
# --------------------------------------------------------------------------

def bms_to_xml(blob: bytes) -> bytes:
    """Encrypted .bms bytes -> UTF-8 XML bytes."""
    if len(blob) % BLOCK:
        raise ValueError(f"not a .bms file: length {len(blob)} is not a multiple of {BLOCK}")
    plain = pkcs7_unpad(aes_cbc(blob, encrypt=False))
    if not plain.lstrip()[:5].startswith(b"<BMS>"):
        raise ValueError("decrypted data does not start with <BMS> — wrong key or corrupt file")
    return plain


def normalise_xml(raw: bytes) -> bytes:
    """Accept UTF-16 (the Diagnostic Software's own export) or UTF-8, with or
    without BOM, and return the UTF-8/no-BOM form the .bms payload uses."""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16").encode("utf-8")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:]
    return raw


def xml_to_bms(raw: bytes) -> bytes:
    """XML bytes -> encrypted .bms bytes, verified by decrypting the result."""
    plain = normalise_xml(raw)
    if not plain.lstrip()[:5].startswith(b"<BMS>"):
        raise ValueError("input does not look like an s-BMS configuration (no <BMS> root)")
    blob = aes_cbc(pkcs7_pad(plain), encrypt=True)
    if bms_to_xml(blob) != plain:
        raise RuntimeError("internal error: round-trip verification failed, refusing to write")
    return blob


def _write(path: str, data: bytes, force: bool) -> None:
    if os.path.exists(path) and not force:
        sys.exit(f"refusing to overwrite existing {path} (pass --force)")
    with open(path, "wb") as fh:
        fh.write(data)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_decrypt(a) -> None:
    blob = open(a.input, "rb").read()
    xml = bms_to_xml(blob)
    out = a.output or os.path.splitext(a.input)[0] + ".xml"
    data = xml.decode("utf-8").encode("utf-16") if a.utf16 else xml
    _write(out, data, a.force)
    print(f"{a.input}  ->  {out}  ({len(data):,} bytes, {'UTF-16' if a.utf16 else 'UTF-8'})")


def cmd_encrypt(a) -> None:
    raw = open(a.input, "rb").read()
    blob = xml_to_bms(raw)
    out = a.output or os.path.splitext(a.input)[0] + ".bms"
    _write(out, blob, a.force)
    print(f"{a.input}  ->  {out}  ({len(blob):,} bytes, round-trip verified)")


def cmd_info(a) -> None:
    for path in a.inputs:
        raw = open(path, "rb").read()
        name = os.path.basename(path)
        try:
            xml = bms_to_xml(raw) if raw[:1] != b"<" and raw[:2] not in (b"\xff\xfe", b"\xfe\xff") \
                else normalise_xml(raw)
            kind = "encrypted .bms" if raw[:1] != b"<" and raw[:2] not in (b"\xff\xfe", b"\xfe\xff") else "plain XML"
        except Exception as exc:
            print(f"{name}\n    unreadable: {exc}")
            continue
        digest = hashlib.sha256(xml).hexdigest()

        def grab(tag: str) -> str:
            i = xml.find(b"<" + tag.encode() + b">")
            if i < 0:
                return "—"
            j = xml.find(b"</", i)
            return xml[i + len(tag) + 2:j].decode("utf-8", "replace")

        print(f"{name}")
        print(f"    {kind}, plaintext {len(xml):,} bytes   sha256 {digest[:16]}")
        print(f"    over-voltage {grab('CellOverVoltage')} mV · target {grab('CellTargetVoltage')} mV · "
              f"min {grab('CellMinimumVoltage')} mV · {grab('BatteryInitialTotalAh')} Ah · "
              f"{grab('NumberOfLMUs')} LMUs")


def cmd_selftest(a) -> None:
    ok = True
    for path in a.inputs:
        blob = open(path, "rb").read()
        name = os.path.basename(path)
        try:
            xml = bms_to_xml(blob)
            again = xml_to_bms(xml)
            good = again == blob
            ok &= good
            print(f"[{'PASS' if good else 'FAIL'}] {name}: decrypt -> re-encrypt reproduces the original")
        except Exception as exc:
            ok = False
            print(f"[FAIL] {name}: {exc}")
    # also confirm the built-in AES agrees with the platform one
    sample = bytes(range(64))
    if _cbc_commoncrypto(sample, KEY, IV, True) is not None:
        same = _cbc_commoncrypto(sample, KEY, IV, True) == _cbc_py(sample, KEY, IV, True)
        ok &= same
        print(f"[{'PASS' if same else 'FAIL'}] built-in AES matches CommonCrypto")
    sys.exit(0 if ok else 1)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Decrypt / encrypt LiBAL s-BMS .bms configuration files.",
        epilog="AES-128-CBC, key 'extremelysecret!', IV 'almostassecret!!' "
               "(recovered from Diagnostic Software 6.18.0).")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("decrypt", help="encrypted .bms -> XML")
    d.add_argument("input")
    d.add_argument("-o", "--output")
    d.add_argument("--utf16", action="store_true",
                   help="write UTF-16 XML, matching the Diagnostic Software's own export")
    d.add_argument("--force", action="store_true", help="overwrite the output file if it exists")
    d.set_defaults(func=cmd_decrypt)

    e = sub.add_parser("encrypt", help="XML -> encrypted .bms")
    e.add_argument("input")
    e.add_argument("-o", "--output")
    e.add_argument("--force", action="store_true", help="overwrite the output file if it exists")
    e.set_defaults(func=cmd_encrypt)

    i = sub.add_parser("info", help="identify and fingerprint config files")
    i.add_argument("inputs", nargs="+")
    i.set_defaults(func=cmd_info)

    s = sub.add_parser("selftest", help="verify decrypt/encrypt round-trips byte for byte")
    s.add_argument("inputs", nargs="+")
    s.set_defaults(func=cmd_selftest)

    a = p.parse_args()
    try:
        a.func(a)
    except (ValueError, RuntimeError) as exc:
        sys.exit(f"error: {exc}")


if __name__ == "__main__":
    main()
