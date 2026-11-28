#include "ArtworkPlayer.h"
#include "ArtworkFormat.h"
#include <LittleFS.h>
#include <string.h>

namespace ArtworkPlayer {
namespace {
using namespace ArtworkFormat;
constexpr char ActivePath[] = "/svinka.svp";
constexpr char StagePath[] = "/svinka.tmp";
Adafruit_ILI9341* tft = nullptr;
void (*redrawCallback)() = nullptr;
bool mounted = false;
size_t storedSize = 0, expectedSize = 0, received = 0;
uint32_t storedCrc = 0, expectedCrc = 0, frameStarted = 0;
Header header{};
uint8_t frameIndex = 0;
// Four expanded RGB565 rows, 2560 bytes, not a full framebuffer.
uint16_t pixels[320 * 4];

void abortTransfer() {
    expectedSize = received = 0;
    expectedCrc = 0;
    if (mounted && LittleFS.exists(StagePath)) LittleFS.remove(StagePath);
}

bool validateFile(const char* path, size_t& length, uint32_t& crc, Header& h) {
    File f = LittleFS.open(path, "r");
    if (!f) return false;
    length = f.size();
    uint8_t buffer[256];
    if (f.read(buffer, HeaderBytes) != HeaderBytes || !parse(buffer, length, h)) return false;
    uint32_t state = update(0xFFFFFFFFu, buffer, HeaderBytes);
    size_t left = length - HeaderBytes - 4;
    while (left) {
        const size_t n = left < sizeof(buffer) ? left : sizeof(buffer);
        if (f.read(buffer, n) != n) return false;
        state = update(state, buffer, n);
        left -= n;
    }
    if (f.read(buffer, 4) != 4) return false;
    crc = u32(buffer);
    return (state ^ 0xFFFFFFFFu) == crc;
}

bool draw(uint8_t index) {
    if (!storedSize || index >= header.count || !tft) return false;
    File f = LittleFS.open(ActivePath, "r");
    if (!f || !f.seek(HeaderBytes + size_t(index) * FrameBytes)) return false;
    uint8_t row[Width];
    for (size_t y = 0; y < Height; ++y) {
        if (f.read(row, Width) != Width) return false;
        for (size_t x = 0; x < Width; ++x) {
            const uint16_t color = rgb565(row[x]);
            for (size_t dx = 0; dx < 4; ++dx) pixels[x*4 + dx] = color;
        }
        for (size_t dy = 1; dy < 4; ++dy) memcpy(pixels + dy*320, pixels, 320*sizeof(uint16_t));
        tft->drawRGBBitmap(0, y*4, pixels, 320, 4);
    }
    return true;
}
void loseArtwork() {
    storedSize = 0;
    storedCrc = 0;
}
void ack(JsonObject response, const char* command) {
    response["type"] = "ack";
    response["command"] = command;
}
void error(JsonObject response, const char* code) {
    response["type"] = "error";
    response["code"] = code;
}
int hexDigit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
}

void begin(Adafruit_ILI9341& display, void (*redraw)()) {
    tft = &display;
    redrawCallback = redraw;
    mounted = LittleFS.begin(false);
    loseArtwork();
    if (!mounted) return;
    abortTransfer();
    size_t size = 0;
    uint32_t crc = 0;
    Header candidate{};
    if (validateFile(ActivePath, size, crc, candidate)) {
        storedSize = size; storedCrc = crc; header = candidate;
    }
}
bool active() { return storedSize != 0; }
bool show() {
    frameIndex = 0;
    if (!active()) return false;
    if (!draw(0)) { loseArtwork(); return false; }
    frameStarted = millis();
    return true;
}
bool showBoop() {
    if (!active() || !header.boop) return false;
    if (!draw(header.count - 1)) { loseArtwork(); return false; }
    return true;
}
void tick() {
    if (!active()) return;
    const uint8_t count = header.count - uint8_t(header.boop);
    if (count <= 1 || uint32_t(millis() - frameStarted) < header.duration) return;
    frameIndex = (frameIndex + 1) % count;
    frameStarted = millis();
    if (!draw(frameIndex)) { loseArtwork(); if (redrawCallback) redrawCallback(); }
}

bool handle(JsonObjectConst request, JsonObject response) {
    const char* command = request["type"] | "";
    if (strncmp(command, "art_", 4) != 0) return false;
    if (strcmp(command, "art_status") == 0) {
        ack(response, command);
        response["available"] = mounted;
        response["present"] = mounted && LittleFS.exists(ActivePath);
        response["size"] = storedSize;
        response["crc32"] = storedCrc;
        return true;
    }
    if (strcmp(command, "art_init") == 0) {
        // Explicit, local provisioning only. Never format automatically on boot.
        if (mounted || strcmp(request["confirm"] | "", "FORMAT_ARTWORK_FS") != 0) {
            error(response, "art_init_not_allowed"); return true;
        }
        mounted = LittleFS.begin(true);
        if (!mounted) { error(response, "art_storage_unavailable"); return true; }
        abortTransfer();
        // begin(true) can mount an existing filesystem without formatting it.
        size_t size = 0; uint32_t crc = 0; Header candidate{};
        if (validateFile(ActivePath, size, crc, candidate)) {
            storedSize = size; storedCrc = crc; header = candidate;
            if (redrawCallback) redrawCallback();
        }
        ack(response, command); return true;
    }
    if (!mounted) { error(response, "art_storage_unavailable"); return true; }
    if (strcmp(command, "art_abort") == 0) { abortTransfer(); ack(response, command); return true; }
    if (strcmp(command, "art_begin") == 0) {
        if (!request["size"].is<uint32_t>() || !request["crc32"].is<uint32_t>()) {
            error(response, "invalid_art_begin"); return true;
        }
        const size_t size = request["size"].as<uint32_t>();
        if (size < HeaderBytes + FrameBytes + 4 || size > MaxBytes) {
            error(response, "invalid_art_size"); return true;
        }
        abortTransfer();
        File f = LittleFS.open(StagePath, "w");
        if (!f) { error(response, "art_storage_error"); return true; }
        f.close(); expectedSize = size; expectedCrc = request["crc32"].as<uint32_t>();
        ack(response, command); return true;
    }
    if (strcmp(command, "art_chunk") == 0) {
        if (!expectedSize || !request["offset"].is<uint32_t>() || request["offset"].as<uint32_t>() != received || !request["data"].is<const char*>()) {
            error(response, "invalid_art_chunk"); return true;
        }
        const JsonString data = request["data"].as<JsonString>();
        const size_t n = data.size();
        uint8_t bytes[200];
        if (!n || n % 2 || n > sizeof(bytes)*2 || n/2 > expectedSize - received) {
            error(response, "invalid_art_chunk"); return true;
        }
        for (size_t i = 0; i < n/2; ++i) {
            const int hi = hexDigit(data.c_str()[i*2]), lo = hexDigit(data.c_str()[i*2+1]);
            if (hi < 0 || lo < 0) { error(response, "invalid_art_chunk"); return true; }
            bytes[i] = uint8_t((hi << 4) | lo);
        }
        File f = LittleFS.open(StagePath, "a");
        if (!f || f.size() != received || f.write(bytes, n/2) != n/2) {
            f.close(); abortTransfer(); error(response, "art_storage_error"); return true;
        }
        f.close(); received += n/2; ack(response, command); return true;
    }
    if (strcmp(command, "art_commit") == 0) {
        size_t size = 0; uint32_t crc = 0; Header candidate{};
        if (!expectedSize || received != expectedSize || !validateFile(StagePath, size, crc, candidate) || size != expectedSize || crc != expectedCrc) {
            abortTransfer(); error(response, "invalid_art_pack"); return true;
        }
        // LittleFS rename replaces an existing regular file atomically. Never delete the old file first.
        if (!LittleFS.rename(StagePath, ActivePath)) { abortTransfer(); error(response, "art_storage_error"); return true; }
        expectedSize = received = 0; expectedCrc = 0;
        storedSize = size; storedCrc = crc; header = candidate;
        if (redrawCallback) redrawCallback();
        ack(response, command); return true;
    }
    if (strcmp(command, "art_clear") == 0) {
        abortTransfer();
        if (LittleFS.exists(ActivePath) && !LittleFS.remove(ActivePath)) { error(response, "art_storage_error"); return true; }
        loseArtwork();
        if (redrawCallback) redrawCallback();
        ack(response, command); return true;
    }
    error(response, "unknown_command"); return true;
}
}
