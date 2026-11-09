#include <DriverKit/IOLib.h>
#include <DriverKit/IOBufferMemoryDescriptor.h>
#include <DriverKit/OSData.h>
#include "OpenLabelUSBUserClient.h"
#include "OpenLabelUSBDriver.h"

struct OpenLabelUSBUserClient_IVars {
    OpenLabelUSBDriver *driver;
    IOBufferMemoryDescriptor *buffer;
    uint64_t expected;
    uint64_t received;
};

bool OpenLabelUSBUserClient::init() {
    if (!super::init()) return false;
    ivars = IONewZero(OpenLabelUSBUserClient_IVars,1);
    return ivars != nullptr;
}

void OpenLabelUSBUserClient::ResetJob() {
    OSSafeReleaseNULL(ivars->buffer);
    ivars->expected = ivars->received = 0;
}

void OpenLabelUSBUserClient::free() {
    if (ivars) {
        ResetJob();
        OSSafeReleaseNULL(ivars->driver);
        IOSafeDeleteNULL(ivars,OpenLabelUSBUserClient_IVars,1);
    }
    super::free();
}

kern_return_t OpenLabelUSBUserClient::Start_Impl(IOService *provider) {
    auto result = Start(provider,SUPERDISPATCH);
    if (result != kIOReturnSuccess) return result;
    ivars->driver = OSDynamicCast(OpenLabelUSBDriver,provider);
    if (!ivars->driver) return kIOReturnBadArgument;
    ivars->driver->retain();
    return kIOReturnSuccess;
}

kern_return_t OpenLabelUSBUserClient::Stop_Impl(IOService *provider) {
    ResetJob();
    return Stop(provider,SUPERDISPATCH);
}

kern_return_t OpenLabelUSBUserClient::ExternalMethod(uint64_t selector,IOUserClientMethodArguments *args,
    const IOUserClientMethodDispatch *,OSObject *,void *) {
    if (!args || !ivars->driver || args->completion || args->structureInputDescriptor)
        return kIOReturnBadArgument;
    const uint64_t inputLength = args->structureInput ? args->structureInput->getLength() : 0;
    switch (selector) {
        case 0: { // Begin a complete job; no bytes reach USB before Commit.
            if (args->scalarInputCount != 1 || !args->scalarInput || inputLength || args->scalarOutputCount)
                return kIOReturnBadArgument;
            if (ivars->buffer) return kIOReturnBusy;
            const auto length = args->scalarInput[0];
            if (!length || length > 131072) return kIOReturnBadArgument;
            auto result = ivars->driver->MakeBuffer(length,&ivars->buffer);
            if (result == kIOReturnSuccess) { ivars->expected = length; ivars->received = 0; }
            return result;
        }
        case 1: { // Small inline chunks avoid unbounded user mappings.
            if (args->scalarInputCount || args->scalarOutputCount || !inputLength || inputLength > 2048 ||
                !ivars->buffer || inputLength > ivars->expected - ivars->received) return kIOReturnBadArgument;
            IOAddressSegment address = {};
            auto result = ivars->buffer->GetAddressRange(&address);
            if (result != kIOReturnSuccess || address.length < ivars->expected) return kIOReturnBadArgument;
            memcpy(reinterpret_cast<uint8_t *>(address.address) + ivars->received,
                args->structureInput->getBytesNoCopy(),inputLength);
            ivars->received += inputLength;
            return kIOReturnSuccess;
        }
        case 2: { // Commit once. Errors discard the job to prevent silent duplicate retries.
            if (inputLength || args->scalarInputCount || args->scalarOutputCount != 1 || !args->scalarOutput ||
                !ivars->buffer || ivars->expected != ivars->received) return kIOReturnBadArgument;
            uint32_t sent = 0;
            auto result = ivars->driver->Send(ivars->buffer,static_cast<uint32_t>(ivars->received),&sent);
            args->scalarOutput[0] = sent;
            ResetJob();
            return result;
        }
        case 3:
            if (inputLength || args->scalarInputCount || args->scalarOutputCount) return kIOReturnBadArgument;
            ResetJob();
            return kIOReturnSuccess;
        default: return kIOReturnUnsupported;
    }
}
