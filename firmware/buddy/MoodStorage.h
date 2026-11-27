
#pragma once

#include <stddef.h>
#include <stdint.h>

#include "Mood.h"


namespace StorageConfig {

    constexpr uint32_t SCHEMA_VERSION = 1;

    constexpr size_t MAX_RECORD_BYTES = 512;
}


// --------------------------------------------------
// Storage backend interface
// --------------------------------------------------

class MoodRecordBackend {

public:

    enum class ReadResult : uint8_t {
        Ok,
        Missing,
        Invalid,
        Unavailable
    };

    virtual ~MoodRecordBackend() = default;

    virtual ReadResult read(
        char* output,
        size_t capacity,
        size_t& length
    ) = 0;

    virtual bool write(
        const char* data,
        size_t length
    ) = 0;
};


// --------------------------------------------------
// Mood persistence
// --------------------------------------------------

class MoodStorage {

public:

    enum class RestoreResult : uint8_t {
        Restored,
        Empty,
        Invalid,
        UnsupportedVersion,
        Unavailable
    };

    explicit MoodStorage(
        MoodRecordBackend& backend
    );

    RestoreResult restore(Mood& output);

    // Accepts an already validated mood
    bool save(const Mood& mood);

    static const char* statusName(
        RestoreResult result
    );

private:

    MoodRecordBackend& backend_;

    char cachedRecord_[
        StorageConfig::MAX_RECORD_BYTES
    ]{};

    size_t cachedLength_ = 0;

    static bool encode(
        const Mood& mood,
        char* output,
        size_t capacity,
        size_t& length
    );
};
