
#pragma once

#include <Preferences.h>

#include "MoodStorage.h"


class PreferencesBackend final
    : public MoodRecordBackend {

public:

    bool begin();

    ReadResult read(
        char* output,
        size_t capacity,
        size_t& length
    ) override;

    bool write(
        const char* data,
        size_t length
    ) override;

private:

    Preferences preferences_;

    bool opened_ = false;
};
