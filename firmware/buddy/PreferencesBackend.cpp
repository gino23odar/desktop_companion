
#include "PreferencesBackend.h"

namespace {

    constexpr char NAMESPACE[] = "desk_buddy";

    constexpr char MOOD_KEY[] = "active_mood";
}


// --------------------------------------------------
// Open the NVS namespace
// --------------------------------------------------

bool PreferencesBackend::begin() {

    if (opened_) {
        return true;
    }

    opened_ = preferences_.begin(
        NAMESPACE,
        false
    );

    return opened_;
}


// --------------------------------------------------
// Read the saved mood
// --------------------------------------------------

MoodRecordBackend::ReadResult
PreferencesBackend::read(
    char* output,
    size_t capacity,
    size_t& length
) {

    length = 0;

    if (!opened_) {

        return ReadResult::Unavailable;
    }

    if (!preferences_.isKey(MOOD_KEY)) {

        return ReadResult::Missing;
    }

    const size_t storedLength =
        preferences_.getBytesLength(MOOD_KEY);

    if (
        storedLength == 0 ||
        storedLength > capacity
    ) {
        return ReadResult::Invalid;
    }

    const size_t bytesRead =
        preferences_.getBytes(
            MOOD_KEY,
            output,
            storedLength
        );

    if (bytesRead != storedLength) {

        return ReadResult::Unavailable;
    }

    length = bytesRead;

    return ReadResult::Ok;
}


// --------------------------------------------------
// Write a complete mood record
// --------------------------------------------------

bool PreferencesBackend::write(
    const char* data,
    size_t length
) {

    if (!opened_) {
        return false;
    }

    if (
        length == 0 ||
        length >= StorageConfig::MAX_RECORD_BYTES
    ) {
        return false;
    }

    const size_t written =
        preferences_.putBytes(
            MOOD_KEY,
            data,
            length
        );

    return written == length;
}
