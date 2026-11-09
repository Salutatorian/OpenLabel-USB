#include <DriverKit/IOLib.h>
#include <DriverKit/IOBufferMemoryDescriptor.h>
#include <USBDriverKit/IOUSBHostInterface.h>
#include <USBDriverKit/IOUSBHostPipe.h>
#include "OpenLabelUSBDriver.h"
#include "OpenLabelUSBUserClient.h"
#include "USBDescriptorScan.h"

struct OpenLabelUSBDriver_IVars {
    IOUSBHostInterface *interface;
    IOUSBHostPipe *pipe;
    bool opened;
};

bool OpenLabelUSBDriver::init() {
    if (!super::init()) return false;
    ivars = IONewZero(OpenLabelUSBDriver_IVars,1);
    return ivars != nullptr;
}

void OpenLabelUSBDriver::free() {
    if (ivars) {
        if (ivars->opened && ivars->interface) ivars->interface->Close(this,0);
        OSSafeReleaseNULL(ivars->pipe);
        OSSafeReleaseNULL(ivars->interface);
        IOSafeDeleteNULL(ivars,OpenLabelUSBDriver_IVars,1);
    }
    super::free();
}

kern_return_t OpenLabelUSBDriver::Start_Impl(IOService *provider) {
    auto result = Start(provider,SUPERDISPATCH);
    if (result != kIOReturnSuccess) return result;
    ivars->interface = OSDynamicCast(IOUSBHostInterface,provider);
    if (!ivars->interface) return kIOReturnNoDevice;
    ivars->interface->retain();
    result = ivars->interface->Open(this,0,nullptr);
    if (result != kIOReturnSuccess) return result;
    ivars->opened = true;
    const auto *config = ivars->interface->CopyConfigurationDescriptor();
    if (!config) return kIOReturnNoDevice;
    const auto *raw = reinterpret_cast<const uint8_t *>(config);
    const uint32_t length = raw[2] | (static_cast<uint32_t>(raw[3]) << 8);
    const auto *interface = ivars->interface->GetInterfaceDescriptor(config);
    const auto endpoint = interface ? OpenLabelBulkOut(raw,length,interface->bInterfaceNumber,interface->bAlternateSetting) : 0;
    IOFree(const_cast<IOUSBConfigurationDescriptor *>(config),length);
    if (!endpoint) return kIOReturnUnsupported;
    result = ivars->interface->CopyPipe(endpoint,&ivars->pipe);
    if (result != kIOReturnSuccess) return result;
    return RegisterService();
}

kern_return_t OpenLabelUSBDriver::Stop_Impl(IOService *provider) {
    if (ivars->opened && ivars->interface) {
        ivars->interface->Close(this,0);
        ivars->opened = false;
    }
    OSSafeReleaseNULL(ivars->pipe);
    return Stop(provider,SUPERDISPATCH);
}

kern_return_t OpenLabelUSBDriver::NewUserClient_Impl(uint32_t type, IOUserClient **client) {
    if (type != 0 || !client) return kIOReturnBadArgument;
    IOService *service = nullptr;
    auto result = Create(this,"UserClientProperties",&service);
    if (result != kIOReturnSuccess) return result;
    *client = OSDynamicCast(OpenLabelUSBUserClient,service);
    if (!*client) { service->release(); return kIOReturnError; }
    return kIOReturnSuccess;
}

kern_return_t OpenLabelUSBDriver::MakeBuffer(uint64_t length, IOBufferMemoryDescriptor **buffer) {
    if (!ivars->opened || !ivars->interface) return kIOReturnNotOpen;
    if (!buffer || !length || length > 131072) return kIOReturnBadArgument;
    auto result = ivars->interface->CreateIOBuffer(kIOMemoryDirectionOut,length,buffer);
    if (result == kIOReturnSuccess) {
        result = (*buffer)->SetLength(length);
        if (result != kIOReturnSuccess) OSSafeReleaseNULL(*buffer);
    }
    return result;
}

kern_return_t OpenLabelUSBDriver::Send(IOBufferMemoryDescriptor *buffer,uint32_t length,uint32_t *sent) {
    if (!sent) return kIOReturnBadArgument;
    *sent = 0;
    if (!ivars->opened || !ivars->pipe) return kIOReturnNotOpen;
    if (!buffer || !length || length > 131072) return kIOReturnBadArgument;
    IOAddressSegment address = {};
    auto result = buffer->GetAddressRange(&address);
    if (result != kIOReturnSuccess || address.length < length) return kIOReturnBadArgument;
    while (*sent < length) {
        const uint32_t remaining = length - *sent;
        result = buffer->SetLength(remaining);
        if (result != kIOReturnSuccess) return result;
        uint32_t count = 0;
        result = ivars->pipe->IO(buffer,remaining,&count,10000);
        if (count > remaining) return kIOReturnOverrun;
        *sent += count;
        if (result != kIOReturnSuccess) return result;
        if (!count) return kIOReturnUnderrun;
        if (*sent < length) memmove(reinterpret_cast<void *>(address.address),
            reinterpret_cast<const uint8_t *>(address.address) + count,length - *sent);
    }
    return kIOReturnSuccess;
}
