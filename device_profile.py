"""Only the MHT-L1081 USB profile has been investigated."""
import re

VID, PID = 0x0FE6, 0x811E

def matches_model(vid, pid, description):
    return (vid, pid) == (VID, PID) and bool(
        re.search(r'(?<![A-Z0-9])MHT-L1081(?![A-Z0-9])', description.strip(), re.I))
