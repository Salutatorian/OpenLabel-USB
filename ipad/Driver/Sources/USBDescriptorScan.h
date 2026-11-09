#pragma once
#include <stddef.h>
#include <stdint.h>

// Parse a complete configuration, selecting only the provider's current interface.
inline uint8_t OpenLabelBulkOut(const uint8_t *bytes, size_t size, uint8_t number, uint8_t alternate) {
    if (!bytes || size < 9 || bytes[0] < 9 || bytes[1] != 2) return 0;
    const size_t total = bytes[2] | (static_cast<size_t>(bytes[3]) << 8);
    if (total > size || total < 9) return 0;
    bool selected = false;
    uint8_t output = 0;
    for (size_t offset = 0; offset < total;) {
        if (total - offset < 2) return 0;
        const size_t length = bytes[offset];
        if (length < 2 || length > total - offset) return 0;
        const auto *item = bytes + offset;
        if (item[1] == 4) {
            if (length < 9) return 0;
            selected = item[2] == number && item[3] == alternate && item[5] == 7;
        } else if (item[1] == 5 && selected) {
            if (length < 7) return 0;
            const uint8_t address = item[2];
            if ((item[3] & 3) == 2 && (address & 0x80) == 0 && (address & 15) != 0)
                output = address;
        }
        offset += length;
    }
    return output;
}
