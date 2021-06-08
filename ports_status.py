import cs
import time
import sys
import logging
import logging.handlers


handlers = [logging.StreamHandler()]

if sys.platform == 'linux2':
    # on router also use the syslog
    handlers.append(logging.handlers.SysLogHandler(address='/dev/log'))

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s: %(message)s',
                    datefmt='%b %d %H:%M:%S',
                    handlers=handlers)

log = logging.getLogger('ports-status')

APP_NAME = 'PORTS_STATUS'
DEBUG = True
MODELS_WITHOUT_WAN = ['CBA', 'W200', 'W400', 'L950', 'IBR200', '4250']

if DEBUG:
    print("DEBUG ENABLED")

if DEBUG:
    print("Getting Model")

"""Get model number, since some models don't have ethernet WAN"""
model = ''
model = cs.CSClient().get('/status/product_info/product_name').get('data')
if DEBUG:
    print(model)

while True:
    try:
        ports_status = ""
        is_available_modem = 0
        is_available_wan = 0
        is_available_wwan = 0
        is_configured_wwan = 0

        wans = cs.CSClient().get('/status/wan/devices').get('data')

        if wans:

            """Get status of ethernet WANs"""
            for wan in (wan for wan in wans if 'ethernet' in wan):

                summary = cs.CSClient().get('/status/wan/devices/{}/status/summary'.format(wan)).get('data')

                if 'connected' in summary:
                    is_available_wan = 1
                    ports_status += "WAN: 🟢 "

                elif 'available' in summary or 'standby' in summary:
                    is_available_wan = 2
                    ports_status += "WAN: 🟡 "

                elif 'error' in summary:
                    continue

            """If no active/standby WANs are found, show offline"""
            if is_available_wan == 0 and not any(x in model for x in MODELS_WITHOUT_WAN):
                ports_status += "WAN: ⚫️ "

            ports_status += "LAN:"

            """Get status of all ethernet ports"""
            for port in cs.CSClient().get('/status/ethernet').get('data'):
                """Ignore ethernet0 (treat as WAN) except for IBR200/CBA"""
                if (port['port'] == 0 and any(x in model for x in MODELS_WITHOUT_WAN)) or (port['port'] >= 1):
                    if port['link'] == "up":
                        ports_status += " 🟢 "
                    else:
                        ports_status += " ⚫️ "

            """Get status of all modems"""
            for wan in (wan for wan in wans if 'mdm' in wan):

                """Filter to only track modems. Will show green if at least one modem is active"""
                if 'mdm' in wan:

                    """Get modem status for each modem"""
                    summary = cs.CSClient().get('/status/wan/devices/{}/status/summary'.format(wan)).get('data')

                    if 'connected' in summary:
                        is_available_modem = 1
                        ports_status += "MDM: 🟢 "

                    elif 'available' in summary or 'standby' in summary:
                        is_available_modem = 2
                        ports_status += "MDM: 🟡 "

                    elif 'error' in summary:
                        continue

            """If no active/standby modems are found, show offline"""
            if is_available_modem == 0:
                ports_status += "MDM: ⚫️ "

            for wan in (wan for wan in wans if 'wwan' in wan):
                is_configured_wwan = 1
                summary = cs.CSClient().get('/status/wan/devices/{}/status/summary'.format(wan)).get('data')

                if summary:

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

            ipverifys = cs.CSClient().get('/status/ipverify').get('data')
            if ipverifys:
                ports_status += "VPN:"

                for ipverify in ipverifys:
                    testpass = cs.CSClient().get('/status/ipverify/{}/pass'.format(ipverify)).get('data')
                    if testpass:
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

    except Exception as err:
        log.error("Failed with exception={} err={}".format(type(err), str(err)))
