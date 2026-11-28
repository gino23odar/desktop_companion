#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include <Adafruit_ILI9341.h>

namespace ArtworkPlayer {
// No formatting on mount failure. Primitive moods remain usable.
void begin(Adafruit_ILI9341& display, void (*redraw)());
bool active();
bool show();           // frame zero and restart animation clock
bool showBoop();       // false if no custom reaction or read failed
void tick();           // invoke only when not booping
// true = recognized art command; response gets type/command or type/code.
// SerialProtocol remains responsible for request_id correlation and sending JSON.
bool handle(JsonObjectConst request, JsonObject response);
}
