#include "Sources/USBDescriptorScan.h"
#include <assert.h>
#include <stdint.h>

int main() {
    uint8_t config[] = {9,2,32,0,1,1,0,0x80,50,
        9,4,0,0,2,7,1,2,0, 7,5,0x81,2,64,0,0, 7,5,2,2,64,0,0};
    assert(OpenLabelBulkOut(config,sizeof(config),0,0) == 2);
    assert(OpenLabelBulkOut(config,sizeof(config),1,0) == 0);
    assert(OpenLabelBulkOut(config,sizeof(config)-1,0,0) == 0);
    config[18] = 0;
    assert(OpenLabelBulkOut(config,sizeof(config),0,0) == 0);
    assert(OpenLabelBulkOut(nullptr,0,0,0) == 0);
}
