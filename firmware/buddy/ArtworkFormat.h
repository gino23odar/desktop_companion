#pragma once
#include <stddef.h>
#include <stdint.h>

namespace ArtworkFormat {
constexpr size_t Width = 80, Height = 60, FrameBytes = Width * Height;
constexpr size_t HeaderBytes = 8, MaxBytes = HeaderBytes + 8 * FrameBytes + 4;
struct Header { uint8_t count; bool boop; uint16_t duration; };
inline uint32_t u32(const uint8_t* b) {
    return uint32_t(b[0]) | uint32_t(b[1]) << 8 | uint32_t(b[2]) << 16 | uint32_t(b[3]) << 24;
}
inline uint32_t update(uint32_t crc, const uint8_t* bytes, size_t n) {
    while (n--) {
        crc ^= *bytes++;
        for (int i = 0; i < 8; ++i) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return crc;
}
inline bool parse(const uint8_t* b, size_t total, Header& h) {
    if (total < HeaderBytes + FrameBytes + 4 || total > MaxBytes ||
        b[0]!='S' || b[1]!='V' || b[2]!='P' || b[3]!='1' || b[4]<1 || b[4]>8 || b[5]>1 || b[4]<=b[5]) return false;
    const uint16_t duration = uint16_t(b[6]) | uint16_t(b[7]) << 8;
    if (duration < 250 || duration > 5000 || total != HeaderBytes + b[4]*FrameBytes + 4) return false;
    h = {b[4], b[5] != 0, duration};
    return true;
}
inline uint16_t rgb565(uint8_t v) {
    const uint16_t r = (v >> 5) * 31u / 7u;
    const uint16_t g = ((v >> 2) & 7u) * 63u / 7u;
    const uint16_t b = (v & 3u) * 31u / 3u;
    return uint16_t((r << 11) | (g << 5) | b);
}
}
