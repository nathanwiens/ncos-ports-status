import cs
import time

APP_NAME = 'PORTS_STATUS'

while 1:
    ports_status = ""

    is_available_modem = 0
    for wan in cs.CSClient().get('/status/wan/devices').get('data'):
        if 'mdm' in wan:
            summary = cs.CSClient().get('/status/wan/devices/{}/status/summary'.format(wan)).get('data')
            if 'connected' in summary:
                is_available_modem = 1
                ports_status += "MDM: 🟢 "
            if 'available' in summary:
                is_available_modem = 1
                ports_status += "MDM: 🟡 "
            if 'error' in summary:
                continue

    if is_available_modem == 0:
        ports_status += "MDM: ⚫️ "

    for port in cs.CSClient().get('/status/ethernet').get('data'):
        if port['port'] is 0:
            ports_status += " WAN: "
            if port['link'] == "up":
                ports_status += " 🟢 "
            elif port['link'] == "down":
                try:
                    sfp = cs.CSClient().get('/status/sfp').get('data')[0]
                except:
                    continue
                if sfp:
                    if sfp['link'] == "up":
                        ports_status += " 🟢 "
                    else:
                        ports_status += " ⚫️ "
        if port['port'] is 1:
            ports_status += " LAN: "
        if port['port'] >= 1:
            if port['link'] == "up":
                ports_status += " 🟢 "
            elif port['link'] == "down":
                ports_status += " ⚫️ "

    cs.CSClient().put('/config/system/desc', ports_status)
    time.sleep(5)
