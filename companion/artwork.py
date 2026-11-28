"""SVP1 pack codec, shared by backend and companion (stdlib only)."""
import base64
import binascii
import struct
import zlib
from .sync_models import validate_publication
from .protocol import ProtocolError

WIDTH, HEIGHT = 80, 60
FRAME_BYTES = WIDTH * HEIGHT
MAX_FRAMES = 8
MAX_PACK_BYTES = 8 + MAX_FRAMES * FRAME_BYTES + 4
MAX_B64 = ((MAX_PACK_BYTES + 2) // 3) * 4
CHUNK_BYTES = 200


def inspect_pack(raw):
    if not isinstance(raw, bytes) or not 8 + FRAME_BYTES + 4 <= len(raw) <= MAX_PACK_BYTES:
        raise ValueError('Invalid artwork length')
    magic, count, boop, duration = struct.unpack_from('<4sBBH', raw)
    if (magic != b'SVP1' or not 1 <= count <= MAX_FRAMES or boop not in (0, 1)
            or count <= boop or not 250 <= duration <= 5000
            or len(raw) != 8 + count * FRAME_BYTES + 4):
        raise ValueError('Invalid artwork header')
    crc = struct.unpack_from('<I', raw, len(raw)-4)[0]
    if zlib.crc32(raw[:-4]) != crc:
        raise ValueError('Invalid artwork checksum')
    return {'size': len(raw), 'crc32': crc, 'frames': count, 'boop': bool(boop), 'duration_ms': duration}


def encode_pack(frames, duration_ms=500, boop=False):
    if type(duration_ms) is not int or type(boop) is not bool or not 1 <= len(frames) <= MAX_FRAMES:
        raise ValueError('Invalid pack settings')
    if any(type(f) is not bytes or len(f) != FRAME_BYTES for f in frames):
        raise ValueError('Invalid frame size')
    if not 250 <= duration_ms <= 5000 or len(frames) <= int(boop):
        raise ValueError('Invalid frame timing or boop')
    body = struct.pack('<4sBBH', b'SVP1', len(frames), int(boop), duration_ms) + b''.join(frames)
    result = body + struct.pack('<I', zlib.crc32(body))
    inspect_pack(result)
    return result


def decode_pack(value):
    if type(value) is not str or len(value) > MAX_B64:
        raise ValueError('Invalid artwork encoding')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError('Invalid artwork encoding') from None
    inspect_pack(raw)
    if base64.b64encode(raw).decode('ascii') != value:
        raise ValueError('Noncanonical artwork encoding')
    return raw


def validate_artwork(value):
    import re
    if type(value) is not dict or set(value) != {'id', 'pack'}:
        raise ValueError('Invalid artwork fields')
    if type(value['id']) is not str or not re.fullmatch(r'[a-z0-9_-]{1,24}', value['id']):
        raise ValueError('Invalid artwork ID')
    decode_pack(value['pack'])
    return dict(value)


def validate_v2(value):
    if type(value) is not dict or set(value) != {'revision', 'mood', 'published_at', 'artwork'}:
        raise ValueError('Invalid v2 publication')
    base = validate_publication({k: value[k] for k in ('revision','mood','published_at')})
    return {**base, 'artwork': None if value['artwork'] is None else validate_artwork(value['artwork'])}


def status(client):
    reply = client.request('art_status')
    if (type(reply.get('available')) is not bool or type(reply.get('present')) is not bool
            or type(reply.get('size')) is not int
            or type(reply.get('crc32')) is not int or not 0 <= reply['crc32'] <= 0xffffffff
            or not 0 <= reply['size'] <= MAX_PACK_BYTES or (reply['size'] == 0 and reply['crc32'] != 0)):
        raise ProtocolError('Invalid artwork status')
    return reply


def apply_artwork(client, raw):
    """Read before write; on ambiguity caller reconnects and reads again."""
    current = status(client)
    if not current['available']:
        if raw is None:
            return False  # Primitive renderer remains usable without LittleFS.
        raise ProtocolError('Artwork storage unavailable')
    wanted = inspect_pack(raw) if raw is not None else {'size': 0, 'crc32': 0}
    def matches(reply):
        return (reply['available'] and reply['present'] == (raw is not None)
                and all(reply[k] == wanted[k] for k in ('size','crc32')))
    if matches(current):
        return False
    if raw is None:
        client.request('art_clear')
    else:
        client.request('art_begin', size=wanted['size'], crc32=wanted['crc32'])
        for offset in range(0, len(raw), CHUNK_BYTES):
            client.request('art_chunk', offset=offset, data=raw[offset:offset+CHUNK_BYTES].hex())
        client.request('art_commit', timeout=5.0)
    if not matches(status(client)):
        raise ProtocolError('Artwork readback mismatch')
    return True
