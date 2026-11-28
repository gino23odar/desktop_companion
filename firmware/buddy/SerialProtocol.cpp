
#include "SerialProtocol.h"
#include "HardwareConfig.h"
#include "ArtworkPlayer.h"

#include <ArduinoJson.h>
#include <cstring>

namespace SerialProtocol {

namespace {

    // Incoming serial buffer
    char inputBuffer[Hardware::SERIAL_BUFFER_SIZE];

    size_t inputLength = 0;

    // When a line is rejected, discard its remaining bytes until the next newline
    const char* discardedLineError = nullptr;

    struct RequestId {
        bool present;
        uint32_t value;
    };

    constexpr RequestId NO_REQUEST_ID = {
        false,
        0
    };


    // --------------------------------------------------
    // Response serialization
    // --------------------------------------------------

    void sendResponse(
        JsonDocument& document,
        RequestId requestId = NO_REQUEST_ID
    ) {

        if (requestId.present) {
            document["request_id"] = requestId.value;
        }

        serializeJson(document, Serial);
        Serial.println();
    }


    void sendError(
        const char* code,
        RequestId requestId = NO_REQUEST_ID
    ) {

        JsonDocument response;

        response["type"] = "error";
        response["code"] = code;

        sendResponse(response, requestId);
    }

    void sendMoodError(
        const char* field,
        RequestId requestId
    ) {

        JsonDocument response;

        response["type"] = "error";

        response["code"] = "invalid_mood";

        response["field"] = field;

        sendResponse(response, requestId);
    }


    void sendHello(RequestId requestId) {

        JsonDocument response;

        response["type"] = "hello";
        response["device"] = DEVICE_NAME;
        response["protocol"] = PROTOCOL_VERSION;
        response["firmware"] = FIRMWARE_VERSION;
        response["artwork"] = 1;

        sendResponse(response, requestId);
    }


    void sendPong(RequestId requestId) {

        JsonDocument response;

        response["type"] = "pong";

        sendResponse(response, requestId);
    }


    void sendInfo(RequestId requestId) {

        JsonDocument response;

        response["type"] = "info";
        response["device"] = DEVICE_NAME;
        response["firmware"] = FIRMWARE_VERSION;
        response["protocol"] = PROTOCOL_VERSION;

        response["width"] = Hardware::SCREEN_WIDTH;
        response["height"] = Hardware::SCREEN_HEIGHT;

        sendResponse(response, requestId);
    }


    void sendAck(
        const char* command,
        RequestId requestId
    ) {

        JsonDocument response;

        response["type"] = "ack";
        response["command"] = command;

        sendResponse(response, requestId);
    }

    void sendMood(
        const Mood& mood,
        RequestId requestId
    ) {

        JsonDocument response;

        response["type"] = "mood";

        JsonObject moodObject =
            response["mood"].to<JsonObject>();

        MoodModel::writeJson(
            moodObject,
            mood
        );

        sendResponse(response, requestId);
    }


    // --------------------------------------------------
    // Message framing
    // --------------------------------------------------

    bool isWhitespace(char character) {

        return character == ' ' ||
               character == '\t' ||
               character == '\r' ||
               character == '\n';
    }


    // ArduinoJson can stop parsing when an object ends
    // Reject additional data after the top-level object
    bool hasSingleObject(
        const char* data,
        size_t length
    ) {

        bool inString = false;
        bool escaped = false;
        bool started = false;

        int depth = 0;

        for (size_t i = 0; i < length; ++i) {

            char character = data[i];

            if (!started) {

                if (isWhitespace(character)) {
                    continue;
                }

                if (character != '{') {
                    return false;
                }

                started = true;
                depth = 1;

                continue;
            }

            if (inString) {

                if (escaped) {
                    escaped = false;
                } else if (character == '\\') {
                    escaped = true;
                } else if (character == '"') {
                    inString = false;
                }

                continue;
            }

            if (depth == 0) {

                if (!isWhitespace(character)) {
                    return false;
                }

                continue;
            }

            if (character == '"') {
                inString = true;

            } else if (character == '{') {
                ++depth;

            } else if (character == '}') {
                --depth;
            }
        }

        return started &&
               depth == 0 &&
               !inString;
    }


    // --------------------------------------------------
    // Command parsing and dispatch
    // --------------------------------------------------

    void processCommand(
        const char* data,
        size_t length,
        const Handlers& handlers
    ) {

        JsonDocument request;

        DeserializationError error = deserializeJson(
            request,
            data,
            length,
            DeserializationOption::NestingLimit(4)
        );

        if (error) {

            sendError("invalid_json");
            return;
        }

        if (!request.is<JsonObject>()) {

            sendError("invalid_request");
            return;
        }

        if (!hasSingleObject(data, length)) {

            sendError("invalid_json");
            return;
        }

        RequestId requestId = NO_REQUEST_ID;

        JsonVariantConst id =
            request["request_id"];

        // A request identifier is optional
        if (!id.isNull()) {

            if (!id.is<uint32_t>()) {

                sendError("invalid_request_id");
                return;
            }

            requestId.present = true;
            requestId.value = id.as<uint32_t>();
        }

        
        JsonVariantConst type = request["type"];

        if (!type.is<const char*>()) {

            sendError("invalid_command", requestId);

            return;
        }

        // --------------------------------------------------
        // Artwork command handling
        // --------------------------------------------------

        JsonDocument artResponse;

        JsonObject artObject = artResponse.to<JsonObject>();

        if (
            ArtworkPlayer::handle(request.as<JsonObjectConst>(), artObject)
        ) {

            sendResponse(
                artResponse,
                requestId
            );

            return;
        }

        // --------------------------------------------------
        // Existing command handling
        // --------------------------------------------------

        if (type == "hello") {


            sendHello(requestId);

        } else if (type == "ping") {

            sendPong(requestId);

        } else if (type == "get_info") {

            sendInfo(requestId);

        } else if (type == "boop") {

            if (handlers.onBoop == nullptr) {

                sendError(
                    "handler_unavailable",
                    requestId
                );

                return;
            }

            handlers.onBoop();

            sendAck("boop", requestId);

        } else if (type == "set_mood") {

            if (handlers.onSetMood == nullptr) {

                sendError(
                    "handler_unavailable",
                    requestId
                );

                return;
            }

            Mood candidate = {};

            JsonVariantConst moodSource =
                request["mood"];

            const char* invalidField =
                MoodModel::parse(
                    moodSource,
                    candidate
                );

            if (invalidField != nullptr) {

                sendMoodError(
                    invalidField,
                    requestId
                );

                return;
            }

            if (!handlers.onSetMood(candidate)) {

                sendError(
                    "storage_error",
                    requestId
                );

                return;
            }

            sendAck("set_mood", requestId);

        } else if (type == "reset_mood") {

            if (handlers.onSetMood == nullptr) {

                sendError(
                    "handler_unavailable",
                    requestId
                );

                return;
            }

            const Mood defaultMood =
                MoodModel::defaultMood();

            if (!handlers.onSetMood(defaultMood)) {

                sendError(
                    "storage_error",
                    requestId
                );

                return;
            }

            sendAck("reset_mood", requestId);

        } else if (type == "get_mood") {

            if (handlers.onGetMood == nullptr) {

                sendError(
                    "handler_unavailable",
                    requestId
                );

                return;
            }

            sendMood(
                handlers.onGetMood(),
                requestId
            );

        } else {

            sendError(
                "unknown_command",
                requestId
            );
        }
    }


    // --------------------------------------------------
    // Incoming byte processing
    // --------------------------------------------------

    void processByte(
        char character,
        const Handlers& handlers
    ) {

        if (character == '\n') {

            if (discardedLineError != nullptr) {

                sendError(discardedLineError);

            } else {

                // Support both LF and CRLF line endings
                if (
                    inputLength > 0 &&
                    inputBuffer[inputLength - 1] == '\r'
                ) {
                    --inputLength;
                }

                if (inputLength > 0) {

                    inputBuffer[inputLength] = '\0';

                    processCommand(
                        inputBuffer,
                        inputLength,
                        handlers
                    );
                }
            }

            inputLength = 0;
            discardedLineError = nullptr;

            return;
        }

        // Ignore the rest of an already rejected line
        if (discardedLineError != nullptr) {
            return;
        }

        // Reject raw null bytes
        if (character == '\0') {

            discardedLineError = "invalid_frame";
            return;
        }

        // Reserve one byte for the null terminator
        if (
            inputLength >= sizeof(inputBuffer) - 1
        ) {

            discardedLineError = "message_too_large";
            return;
        }

        inputBuffer[inputLength++] = character;
    }

} // Anonymous namespace


// --------------------------------------------------
// Public interface
// --------------------------------------------------

void poll(const Handlers& handlers) {

    size_t processed = 0;

    while (
        Serial.available() > 0 &&
        processed < Hardware::SERIAL_BYTES_PER_LOOP
    ) {

        int incoming = Serial.read();

        if (incoming < 0) {
            break;
        }

        processByte(
            static_cast<char>(incoming),
            handlers
        );

        ++processed;
    }
}


void emitReady() {

    JsonDocument response;

    response["type"] = "ready";
    response["device"] = DEVICE_NAME;
    response["firmware"] = FIRMWARE_VERSION;
    response["protocol"] = PROTOCOL_VERSION;

    sendResponse(response);
}


void emitBoopEvent() {

    JsonDocument response;

    response["type"] = "event";
    response["event"] = "boop";
    response["source"] = "touch";

    sendResponse(response);
}

void emitStorageStatus(
    const char* status
) {

    JsonDocument response;

    response["type"] = "event";

    response["event"] = "storage";

    response["status"] = status;

    sendResponse(response);
}

} // namespace SerialProtocol
