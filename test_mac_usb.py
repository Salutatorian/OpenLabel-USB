import unittest
from unittest.mock import Mock, patch
from mac_usb import _bulk_output, devices, send_raw

class MacUSBTests(unittest.TestCase):
    def test_bulk_endpoint_discovery(self):
        endpoint = Mock(bEndpointAddress=2, bmAttributes=2)
        interface = Mock(bInterfaceClass=7, bAlternateSetting=0, bInterfaceNumber=3)
        interface.__iter__ = Mock(return_value=iter([endpoint]))
        self.assertEqual(_bulk_output([interface]), (3, 2))

    def test_missing_endpoint(self):
        with self.assertRaises(OSError):
            _bulk_output([])

    def test_model_filter_and_resource_cleanup(self):
        dev = Mock(idVendor=0x0fe6, idProduct=0x811e, product='MHT-L1081', bus=1, address=2)
        with patch('mac_usb.backend', return_value=Mock()), patch('usb.core.find', return_value=[dev]), patch('usb.util.dispose_resources') as cleanup:
            self.assertEqual(devices(), ['usb:1:2'])
            cleanup.assert_called_once_with(dev)

    def test_send_claims_and_releases_interface(self):
        dev = Mock(idVendor=0x0fe6, idProduct=0x811e, product='MHT-L1081', bus=1, address=2)
        dev.write.return_value = 3
        with patch('mac_usb.backend', return_value=Mock()), patch('usb.core.find', return_value=[dev]), patch('mac_usb._bulk_output', return_value=(0, 2)), patch('usb.util.claim_interface') as claim, patch('usb.util.release_interface') as release, patch('usb.util.dispose_resources') as cleanup:
            self.assertEqual(send_raw('usb:1:2', b'abc'), 3)
            claim.assert_called_once_with(dev, 0)
            release.assert_called_once_with(dev, 0)
            cleanup.assert_called_once_with(dev)

if __name__ == '__main__':
    unittest.main()
