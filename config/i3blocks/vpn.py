#!/usr/bin/python3
import os
import re
import datetime
import sys
import subprocess
import traceback

ACTIVE_REGEX = re.compile('GENERAL\.STATE:\s*activated')
VPN_NAME = 'Tempo VPN'
DISCONNECT_CONFIRM_FILE = '/tmp/vpn-confirm-file'
dateformat = '%Y%m%d%H%M%S'


def get_disconnect_date():
    if os.path.isfile(DISCONNECT_CONFIRM_FILE):
        with open(DISCONNECT_CONFIRM_FILE, 'r') as f:
            return datetime.datetime.strptime(f.read(), dateformat)


def set_disconnect_date(date):
    with open(DISCONNECT_CONFIRM_FILE, 'w') as f:
        f.write(date.strftime(dateformat))


def updown_vpn(active):
    try:
        p = subprocess.Popen(
            ['nmcli', 'c', 'down' if active else 'up', 'id', VPN_NAME],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        o, e = p.communicate()
    except Exception:
        logfile = os.path.join(os.path.dirname(__file__), 'error_log')
        with open(logfile, 'w') as f:
            f.write(traceback.format_exc())


def handle_click(active, btn):
    if not active:
        updown_vpn(False)
        return handle_show(True)
    else:
        if btn == 1:
            last_click = get_disconnect_date() or datetime.datetime.min
            diff = datetime.datetime.now() - last_click
            if diff.seconds < 5:
                # We clicked again within 5 seconds, terminate
                updown_vpn(True)
                return handle_show(False)
            else:
                set_disconnect_date(datetime.datetime.now())
                print('Click again to terminate the connection!')
                print('Click again to terminate the connection!')
                print('#FF0000')
    return 0


def handle_show(active):
    if active:
        status = 'up'
        color = '#00FF00'
    else:
        status = 'down'
        color = '#FF0000'
    for i in range(2):
        print('VPN: {}'.format(status))
    print(color)


def is_active():
    action = subprocess.Popen(
        ['nmcli', 'con', 'show', 'id', VPN_NAME],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = action.communicate()
    lines = out.decode('utf-8').split('\n')
    for line in lines:
        if ACTIVE_REGEX.search(line):
            return True


def main():
    active = is_active()
    if os.environ.get('BLOCK_BUTTON'):
        handle_click(active, int(os.environ['BLOCK_BUTTON']))
    else:
        handle_show(active)
    return 0


if __name__ == '__main__':
    sys.exit(main())
