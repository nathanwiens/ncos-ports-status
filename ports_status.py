import cs
import time

APP_NAME = 'PORTS_STATUS'
DEBUG = False

if DEBUG:
    print("DEBUG ENABLED")

if DEBUG:
    print("Getting Model")
"""Get model number, since IBR200 doesn't have ethernet WAN"""
model = cs.CSClient().get('/config/system/admin/product_name').get('data')
if DEBUG:
    print(model)

while 1:
    ports_status = ""
    is_available_modem = 0
    sfp = ''
    try:
        sfp = cs.CSClient().get('/status/wan/devices/ethernet-sfp0/status').get('data')
    except:
        if DEBUG:
            print("Couldn't get SFP WAN Status")

    """Get status of all WAN devices"""
    for wan in cs.CSClient().get('/status/wan/devices').get('data'):

        """Filter to only track modems. Will show green if at least one modem is active"""
        if 'mdm' in wan:

            """Get modem status for each modem"""
            summary = cs.CSClient().get('/status/wan/devices/{}/status/summary'.format(wan)).get('data')

            if 'connected' in summary:
                is_available_modem = 1
                ports_status += "MDM: 🟢 "

                """Stop checking if active modem is found"""
                break

            elif 'available' in summary:
                is_available_modem = 1
                ports_status += "MDM: 🟡 "
                """If standby modem found, keep checking for an active one"""
                continue

            elif 'error' in summary:
                continue

    """If no active/standby modems are found, show offline"""
    if is_available_modem == 0:
        ports_status += "MDM: ⚫️ "

    """Get status of all ethernet ports"""
    for port in cs.CSClient().get('/status/ethernet').get('data'):
        """Add WAN label, except for IBR200 which doesn't have ethernet WAN"""
        if port['port'] is 0 and 'IBR200' not in model:
            ports_status += " WAN: "
        elif (port['port'] is 1) or (port['port'] is 0 and 'IBR200' in model):
            """Add LAN label, starting at port 0 for IBR200 and port 1 for all others"""
            ports_status += " LAN: "

        if port['link'] == "up":
            ports_status += " 🟢 "
        elif (port['port'] is 0 and 'IBR200' not in model) and port['link'] == "down":
            """If Ethernet WAN is down, check for SFP WAN"""
            if sfp:
                if sfp['connection_state'] == "connected":
                    ports_status += " 🟢 "
                else:
                    ports_status += " ⚫️ "
        else:
            ports_status += " ⚫️ "

    """Write string to description field"""
    if DEBUG:
        print("WRITING DESCRIPTION")
        print(ports_status)
    cs.CSClient().put('/config/system/desc', ports_status)
    """Wait 5 seconds before checking again"""
    time.sleep(5)
