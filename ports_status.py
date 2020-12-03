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
    is_available_wan = 0
    is_available_wwan = 0
    is_configured_wwan = 0

    wans = cs.CSClient().get('/status/wan/devices').get('data')
    """Get status of all modems"""
    for wan in (wan for wan in wans if 'mdm' in wan):

        """Filter to only track modems. Will show green if at least one modem is active"""
        if 'mdm' in wan:

            """Get modem status for each modem"""
            summary = cs.CSClient().get('/status/wan/devices/{}/status/summary'.format(wan)).get('data')

            if 'connected' in summary:
                is_available_modem = 1
                ports_status += "MDM: 🟢 "
                """Stop checking if active modem is found"""
                break

            elif 'available' in summary or 'standby' in summary:
                is_available_modem = 2
                ports_status += "MDM: 🟡 "
                """If standby modem found, keep checking for an active one"""
                continue

            elif 'error' in summary:
                continue

    """If no active/standby modems are found, show offline"""
    if is_available_modem == 0:
        ports_status += "MDM: ⚫️ "

    for wan in (wan for wan in wans if 'wwan' in wan):
        is_configured_wwan = 1
        summary = cs.CSClient().get('/status/wan/devices/{}/status/summary'.format(wan)).get('data')

        if 'connected' in summary:
            is_available_wwan = 1
            ports_status += "WWAN: 🟢 "
            """Stop checking if active WWAN is found"""
            break

        elif 'available' in summary or 'standby' in summary:
            is_available_wwan = 2
            ports_status += "WWAN: 🟡 "
            """If standby WWAN found, keep checking for an active one"""
            continue

        elif 'error' in summary:
            continue

    """If no active/standby WANs are found, show offline"""
    if is_available_wwan == 0 and is_configured_wwan == 1:
        ports_status += "WWAN: ⚫️ "

    """Get status of ethernet WANs"""
    for wan in (wan for wan in wans if 'ethernet' in wan):

        summary = cs.CSClient().get('/status/wan/devices/{}/status/summary'.format(wan)).get('data')

        if 'connected' in summary:
            is_available_wan = 1
            ports_status += "WAN: 🟢 "
            """Stop checking if active WAN is found"""
            break

        elif 'available' in summary or 'standby' in summary:
            is_available_wan = 2
            ports_status += "WAN: 🟡 "
            """If standby WAN found, keep checking for an active one"""
            continue

        elif 'error' in summary:
            continue

    """If no active/standby WANs are found, show offline"""
    if is_available_wan == 0 and 'IBR200' not in model:
        ports_status += "WAN: ⚫️ "

    ports_status += "LAN:"

    """Get status of all ethernet ports"""
    for port in cs.CSClient().get('/status/ethernet').get('data'):
        """Ignore ethernet0 (treat as WAN) except for IBR200"""
        if (port['port'] >= 1) or (port['port'] is 0 and 'IBR200' in model):

            if port['link'] == "up":
                ports_status += " 🟢 "
            else:
                ports_status += " ⚫️ "

    """Write string to description field"""
    if DEBUG:
        print("WRITING DESCRIPTION")
        print(ports_status)
    cs.CSClient().put('/config/system/desc', ports_status)
    """Wait 5 seconds before checking again"""
    time.sleep(5)
