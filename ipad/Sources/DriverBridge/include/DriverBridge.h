#pragma once
#include <stdint.h>
#include <stddef.h>

int32_t OLDriverStatus(void);
int32_t OLPrintLabel(const uint8_t *bytes, size_t length, uint64_t *sent);
