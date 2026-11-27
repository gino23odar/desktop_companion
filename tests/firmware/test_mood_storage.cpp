
#include "MoodStorage.h"

#include <cassert>
#include <cstring>
#include <iostream>
#include <string>


// --------------------------------------------------
// Fake flash storage
// --------------------------------------------------

class FakeBackend final
    : public MoodRecordBackend {

public:

    std::string record;

    bool hasRecord = false;

    bool available = true;

    bool failWrites = false;

    unsigned writeAttempts = 0;


    ReadResult read(
        char* output,
        size_t capacity,
        size_t& length
    ) override {

        length = 0;

        if (!available) {

            return ReadResult::Unavailable;
        }

        if (!hasRecord) {

            return ReadResult::Missing;
        }

        if (
            record.empty() ||
            record.size() > capacity
        ) {
            return ReadResult::Invalid;
        }

        memcpy(
            output,
            record.data(),
            record.size()
        );

        length = record.size();

        return ReadResult::Ok;
    }


    bool write(
        const char* data,
        size_t length
    ) override {

        ++writeAttempts;

        if (
            !available ||
            failWrites
        ) {
            return false;
        }

        record.assign(data, length);

        hasRecord = true;

        return true;
    }
};


// --------------------------------------------------
// Test helpers
// --------------------------------------------------

Mood customMood() {

    Mood mood = MoodModel::defaultMood();

    strcpy(mood.id, "sleepy");

    strcpy(
        mood.message,
        "Buenas noches"
    );

    mood.background = 0x24243D;

    mood.eyes = EyeStyle::Sleepy;

    mood.mouth = MouthStyle::Neutral;

    mood.blush = true;

    mood.accessory = Accessory::Zzz;

    mood.animation = {
        2000,
        false,
        true
    };

    return mood;
}


bool sameMood(
    const Mood& a,
    const Mood& b
) {

    return
        strcmp(a.id, b.id) == 0 &&
        a.background == b.background &&
        a.eyes == b.eyes &&
        a.mouth == b.mouth &&
        a.blush == b.blush &&
        a.accessory == b.accessory &&
        strcmp(a.message, b.message) == 0 &&
        a.animation.blinkMs ==
            b.animation.blinkMs &&
        a.animation.earWiggle ==
            b.animation.earWiggle &&
        a.animation.accessoryMotion ==
            b.animation.accessoryMotion;
}


void replaceText(
    std::string& record,
    const std::string& before,
    const std::string& after
) {

    const size_t position =
        record.find(before);

    assert(position != std::string::npos);

    record.replace(
        position,
        before.size(),
        after
    );
}


// --------------------------------------------------
// Test 1: Fresh device
// --------------------------------------------------

void testEmptyStorage() {

    FakeBackend backend;

    MoodStorage storage(backend);

    Mood restored = customMood();

    assert( storage.restore(restored) == MoodStorage::RestoreResult::Empty );

    assert(
        sameMood(
            restored,
            MoodModel::defaultMood()
        )
    );

    assert(backend.writeAttempts == 0);
}


// --------------------------------------------------
// Test 2: Complete round trip
// --------------------------------------------------

void testRoundTrip() {

    FakeBackend backend;

    MoodStorage firstBoot(backend);

    const Mood original = customMood();

    assert(firstBoot.save(original));

    assert(backend.writeAttempts == 1);

    // Simulate losing RAM and restarting
    MoodStorage secondBoot(backend);

    Mood restored{};

    assert( secondBoot.restore(restored) == MoodStorage::RestoreResult::Restored );

    assert(sameMood(original, restored));

    assert(backend.writeAttempts == 1);
}


// --------------------------------------------------
// Test 3: Duplicate updates
// --------------------------------------------------

void testDuplicateWrites() {

    FakeBackend backend;

    MoodStorage storage(backend);

    const Mood mood = customMood();

    assert(storage.save(mood));

    for (int i = 0; i < 100; ++i) {

        assert(storage.save(mood));
    }

    assert(backend.writeAttempts == 1);
}


// --------------------------------------------------
// Test 4: Duplicate after restart
// --------------------------------------------------

void testDuplicateAfterRestart() {

    FakeBackend backend;

    MoodStorage firstBoot(backend);

    const Mood original = customMood();

    assert(firstBoot.save(original));

    MoodStorage secondBoot(backend);

    Mood restored{};

    assert(
        secondBoot.restore(restored) ==
        MoodStorage::RestoreResult::Restored
    );

    assert(secondBoot.save(original));

    assert(backend.writeAttempts == 1);
}


// --------------------------------------------------
// Test 5: Changed content, same ID
// --------------------------------------------------

void testChangedContent() {

    FakeBackend backend;

    MoodStorage storage(backend);

    Mood mood = customMood();

    assert(storage.save(mood));

    strcpy(
        mood.message,
        "Dulces suenos"
    );

    assert(storage.save(mood));

    mood.animation.blinkMs = 5000;

    assert(storage.save(mood));

    assert(backend.writeAttempts == 3);

    MoodStorage restarted(backend);

    Mood restored{};

    assert( restarted.restore(restored) == MoodStorage::RestoreResult::Restored );

    assert(sameMood(mood, restored));
}


// --------------------------------------------------
// Test 6: Malformed record
// --------------------------------------------------

void testMalformedRecord() {

    FakeBackend backend;

    backend.hasRecord = true;

    backend.record = "{\"schema\":1";

    MoodStorage storage(backend);

    Mood restored{};

    assert(
        storage.restore(restored) ==
        MoodStorage::RestoreResult::Invalid
    );

    assert(
        sameMood(
            restored,
            MoodModel::defaultMood()
        )
    );

    // Restoration must not automatically erase data
    assert(backend.writeAttempts == 0);

    // A subsequent valid update repairs storage
    assert(storage.save(customMood()));

    MoodStorage restarted(backend);

    assert(
        restarted.restore(restored) ==
        MoodStorage::RestoreResult::Restored
    );

    assert(sameMood(restored, customMood()));
}


// --------------------------------------------------
// Test 7: Invalid saved mood
// --------------------------------------------------

void testInvalidSavedMood() {

    FakeBackend backend;

    MoodStorage storage(backend);

    assert(storage.save(customMood()));

    replaceText(
        backend.record,
        "\"eyes\":\"sleepy\"",
        "\"eyes\":\"laser\""
    );

    MoodStorage restarted(backend);

    Mood restored{};

    assert(
        restarted.restore(restored) ==
        MoodStorage::RestoreResult::Invalid
    );

    assert(
        sameMood(
            restored,
            MoodModel::defaultMood()
        )
    );
}


// --------------------------------------------------
// Test 8: Unsupported schema version
// --------------------------------------------------

void testUnsupportedVersion() {

    FakeBackend backend;

    MoodStorage storage(backend);

    assert(storage.save(customMood()));

    replaceText(
        backend.record,
        "\"schema\":1",
        "\"schema\":2"
    );

    MoodStorage restarted(backend);

    Mood restored{};

    assert(
        restarted.restore(restored) ==
        MoodStorage::RestoreResult::UnsupportedVersion
    );

    assert(
        sameMood(
            restored,
            MoodModel::defaultMood()
        )
    );

    assert(backend.writeAttempts == 1);
}


// --------------------------------------------------
// Test 9: Oversized record
// --------------------------------------------------

void testOversizedRecord() {

    FakeBackend backend;

    backend.hasRecord = true;

    backend.record.assign(
        StorageConfig::MAX_RECORD_BYTES + 1,
        'A'
    );

    MoodStorage storage(backend);

    Mood restored{};

    assert(
        storage.restore(restored) ==
        MoodStorage::RestoreResult::Invalid
    );
}


// --------------------------------------------------
// Test 10: Trailing data
// --------------------------------------------------

void testTrailingData() {

    FakeBackend backend;

    MoodStorage storage(backend);

    assert(storage.save(customMood()));

    backend.record += "garbage";

    MoodStorage restarted(backend);

    Mood restored{};

    assert(
        restarted.restore(restored) ==
        MoodStorage::RestoreResult::Invalid
    );
}


// --------------------------------------------------
// Test 11: Failed write and retry
// --------------------------------------------------

void testFailedWrite() {

    FakeBackend backend;

    MoodStorage storage(backend);

    const Mood original = customMood();

    assert(storage.save(original));

    const std::string previousRecord =
        backend.record;

    Mood replacement = original;

    strcpy(
        replacement.message,
        "New message"
    );

    backend.failWrites = true;

    assert(!storage.save(replacement));

    assert(
        backend.record ==
        previousRecord
    );

    backend.failWrites = false;

    assert(storage.save(replacement));

    assert(backend.writeAttempts == 3);

    MoodStorage restarted(backend);

    Mood restored{};

    assert(
        restarted.restore(restored) ==
        MoodStorage::RestoreResult::Restored
    );

    assert(sameMood(restored, replacement));
}


// --------------------------------------------------
// Test 12: Reset saved mood
// --------------------------------------------------

void testResetMood() {

    FakeBackend backend;

    MoodStorage storage(backend);

    assert(storage.save(customMood()));

    const Mood defaultMood =
        MoodModel::defaultMood();

    assert(storage.save(defaultMood));

    assert(storage.save(defaultMood));

    assert(backend.writeAttempts == 2);

    MoodStorage restarted(backend);

    Mood restored{};

    assert(
        restarted.restore(restored) ==
        MoodStorage::RestoreResult::Restored
    );

    assert(sameMood(restored, defaultMood));
}


// --------------------------------------------------
// Test 13: Unavailable storage
// --------------------------------------------------

void testUnavailableStorage() {

    FakeBackend backend;

    backend.available = false;

    MoodStorage storage(backend);

    Mood restored{};

    assert(
        storage.restore(restored) ==
        MoodStorage::RestoreResult::Unavailable
    );

    assert(
        sameMood(
            restored,
            MoodModel::defaultMood()
        )
    );

    assert(!storage.save(customMood()));
}


// --------------------------------------------------
// Execute all tests
// --------------------------------------------------

int main() {

    testEmptyStorage();

    testRoundTrip();

    testDuplicateWrites();

    testDuplicateAfterRestart();

    testChangedContent();

    testMalformedRecord();

    testInvalidSavedMood();

    testUnsupportedVersion();

    testOversizedRecord();

    testTrailingData();

    testFailedWrite();

    testResetMood();

    testUnavailableStorage();

    std::cout
        << "All 13 mood storage tests passed\n";

    return 0;
}
