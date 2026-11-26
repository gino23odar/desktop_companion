
#include "MoodStorage.h"

#include <ArduinoJson.h>
#include <cstring>


MoodStorage::MoodStorage(
    MoodRecordBackend& backend
) : backend_(backend) {
}


// --------------------------------------------------
// Serialize a complete storage record
// --------------------------------------------------

bool MoodStorage::encode(
    const Mood& mood,
    char* output,
    size_t capacity,
    size_t& length
) {

    length = 0;

    JsonDocument document;

    document["schema"] =
        StorageConfig::SCHEMA_VERSION;

    JsonObject moodObject =
        document["mood"].to<JsonObject>();

    MoodModel::writeJson(
        moodObject,
        mood
    );

    if (document.overflowed()) {
        return false;
    }

    const size_t required =
        measureJson(document);

    // Reserve space for the null terminator
    if (
        required == 0 ||
        required >= capacity
    ) {
        return false;
    }

    const size_t written = serializeJson(
        document,
        output,
        capacity
    );

    if (written != required) {
        return false;
    }

    output[written] = '\0';

    length = written;

    return true;
}


// --------------------------------------------------
// Restore a saved mood
// --------------------------------------------------

MoodStorage::RestoreResult MoodStorage::restore(
    Mood& output
) {

    // Safe fallback for every failure path.
    output = MoodModel::defaultMood();

    cachedLength_ = 0;

    char record[
        StorageConfig::MAX_RECORD_BYTES
    ];

    size_t length = 0;

    const auto result = backend_.read(
        record,
        sizeof(record) - 1,
        length
    );

    switch (result) {

        case MoodRecordBackend::ReadResult::Missing:

            return RestoreResult::Empty;

        case MoodRecordBackend::ReadResult::Invalid:

            return RestoreResult::Invalid;

        case MoodRecordBackend::ReadResult::Unavailable:

            return RestoreResult::Unavailable;

        case MoodRecordBackend::ReadResult::Ok:

            break;
    }

    if (
        length == 0 ||
        length >= sizeof(record) ||
        memchr(record, '\0', length) != nullptr
    ) {
        return RestoreResult::Invalid;
    }

    record[length] = '\0';

    JsonDocument document;

    const DeserializationError error =
        deserializeJson(
            document,
            record,
            length,
            DeserializationOption::NestingLimit(4)
        );

    if (
        error ||
        !document.is<JsonObject>()
    ) {
        return RestoreResult::Invalid;
    }

    if (!document["schema"].is<uint32_t>()) {

        return RestoreResult::Invalid;
    }

    const uint32_t schema =
        document["schema"].as<uint32_t>();

    if (
        schema !=
        StorageConfig::SCHEMA_VERSION
    ) {
        return RestoreResult::UnsupportedVersion;
    }

    if (document.size() != 2) {

        return RestoreResult::Invalid;
    }

    Mood candidate{};

    const char* invalidField =
        MoodModel::parse(
            document["mood"],
            candidate
        );

    if (invalidField != nullptr) {

        return RestoreResult::Invalid;
    }

    // Our own writer produces a canonical record
    // Re-encode to reject trailing bytes and other unexpected modifications
    size_t canonicalLength = 0;

    if (
        !encode(
            candidate,
            cachedRecord_,
            sizeof(cachedRecord_),
            canonicalLength
        )
    ) {
        return RestoreResult::Invalid;
    }

    if (
        canonicalLength != length ||
        memcmp(
            record,
            cachedRecord_,
            length
        ) != 0
    ) {
        return RestoreResult::Invalid;
    }

    cachedLength_ = canonicalLength;

    output = candidate;

    return RestoreResult::Restored;
}


// --------------------------------------------------
// Save an accepted mood
// --------------------------------------------------

bool MoodStorage::save(const Mood& mood) {

    char record[
        StorageConfig::MAX_RECORD_BYTES
    ];

    size_t length = 0;

    if (
        !encode(
            mood,
            record,
            sizeof(record),
            length
        )
    ) {
        return false;
    }

    // Do not write identical records repeatedly
    if (
        cachedLength_ == length &&
        memcmp(
            cachedRecord_,
            record,
            length
        ) == 0
    ) {
        return true;
    }

    // Update the cache only after a successful write
    if (!backend_.write(record, length)) {

        // A failed write leaves storage state uncertain
        // Force the next save to attempt a real write
        cachedLength_ = 0;

        return false;
    }

    memcpy(
        cachedRecord_,
        record,
        length + 1
    );

    cachedLength_ = length;

    return true;
}


// --------------------------------------------------
// Diagnostic status names
// --------------------------------------------------

const char* MoodStorage::statusName(
    RestoreResult result
) {

    switch (result) {

        case RestoreResult::Restored:
            return "restored";

        case RestoreResult::Empty:
            return "empty";

        case RestoreResult::Invalid:
            return "invalid";

        case RestoreResult::UnsupportedVersion:
            return "unsupported_version";

        case RestoreResult::Unavailable:
            return "unavailable";
    }

    return "unknown";
}
