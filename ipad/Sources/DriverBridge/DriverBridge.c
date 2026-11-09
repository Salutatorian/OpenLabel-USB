#include "DriverBridge.h"
#include <IOKit/IOKitLib.h>

static kern_return_t open_driver(io_connect_t *connection) {
    io_service_t service = IOServiceGetMatchingService(kIOMainPortDefault,IOServiceNameMatching("OpenLabelUSBDriver"));
    if (!service) return kIOReturnNotFound;
    kern_return_t result = IOServiceOpen(service,mach_task_self(),0,connection);
    IOObjectRelease(service);
    return result;
}

int32_t OLDriverStatus(void) {
    io_connect_t connection = IO_OBJECT_NULL;
    kern_return_t result = open_driver(&connection);
    if (connection) IOServiceClose(connection);
    return result;
}

int32_t OLPrintLabel(const uint8_t *bytes,size_t length,uint64_t *sent) {
    if (!bytes || !sent || !length || length > 131072) return kIOReturnBadArgument;
    *sent = 0;
    io_connect_t connection = IO_OBJECT_NULL;
    kern_return_t result = open_driver(&connection);
    if (result != kIOReturnSuccess) return result;
    uint64_t expected = length;
    result = IOConnectCallScalarMethod(connection,0,&expected,1,NULL,NULL);
    for (size_t offset = 0; result == kIOReturnSuccess && offset < length;) {
        const size_t chunk = length - offset > 2048 ? 2048 : length - offset;
        size_t output = 0;
        result = IOConnectCallStructMethod(connection,1,bytes+offset,chunk,NULL,&output);
        offset += chunk;
    }
    if (result == kIOReturnSuccess) {
        uint32_t outputCount = 1;
        result = IOConnectCallScalarMethod(connection,2,NULL,0,sent,&outputCount);
        if (result == kIOReturnSuccess && *sent != length) result = kIOReturnUnderrun;
    }
    if (result != kIOReturnSuccess) IOConnectCallScalarMethod(connection,3,NULL,0,NULL,NULL);
    IOServiceClose(connection);
    return result;
}
