#!/usr/bin/python3
import os
import sys
import subprocess
import traceback

OVPN_DIR = '/proc/sys/net/ipv4/conf/vpn0'
VPNC_PID = '/var/run/vpnc.pid'
STATE_FILE = os.path.join(os.path.dirname(__file__), 'vpn_block_state')
DISCONNECT_CONFIRM_FILE = os.path.join(
    os.path.dirname(__file__), 'disconnect_confirm_file'
)

AVAILABLE_CONNECTIONS = [
    ('Trackwell', 'ovpn'),
    ('IKEA', 'ovpn'),
    ('festi', 'vpnc')
]


def ovpn(updown, con_id):
    try:
        p = subprocess.Popen(
            ['nmcli', 'c', updown, 'id', con_id],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        o, e = p.communicate()
    except Exception:
        logfile = os.path.join(os.path.dirname(__file__), 'error_log')
        with open(logfile, 'w') as f:
            f.write(traceback.format_exc())


def log(s):
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'vpn_log')
    with open(LOG_FILE, 'a') as f:
        f.write(str(s))
        f.write('\n')


def get_cur():
    if os.path.isfile(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            current = f.read()
            for i, con in enumerate(AVAILABLE_CONNECTIONS):
                if con[0] == current:
                    return i, con[0]
    return 0, ''


def handle_click(active, btn):
    show_idx, name = get_cur()
    if not active:
        if btn == 1:
            show_idx += 1
            if show_idx >= len(AVAILABLE_CONNECTIONS):
                show_idx = 0
            with open(STATE_FILE, 'w') as f:
                f.write(AVAILABLE_CONNECTIONS[show_idx][0])
            print(AVAILABLE_CONNECTIONS[show_idx][0])
        elif btn in (2, 3):
            name, con_type = AVAILABLE_CONNECTIONS[show_idx]
            if con_type == 'ovpn':
                ovpn('up', name)
            handle_show(True)
        else:
            handle_show(active)
    elif btn == 1:
        if os.path.isfile(DISCONNECT_CONFIRM_FILE):
            os.remove(DISCONNECT_CONFIRM_FILE)
            name, con_type = AVAILABLE_CONNECTIONS[show_idx]
            if con_type == 'ovpn':
                ovpn('down', name)
            handle_show(False)
        else:
            with open(DISCONNECT_CONFIRM_FILE, 'w') as f:
                f.write('1')
            print('Click again to terminate the connection!')
            print('Click again to terminate the connection!')
            print('#FF0000')
    return 0


def handle_show(active):
    if active:
        status = get_cur()[1]
        color = '#00FF00'
    else:
        status = 'down'
        color = '#FF0000'
    for i in range(2):
        print('VPN: {}'.format(status))
    print(color)


def main():
    active = os.path.isdir(OVPN_DIR) or os.path.isfile(VPNC_PID)
    if os.environ.get('BLOCK_BUTTON'):
        handle_click(active, int(os.environ['BLOCK_BUTTON']))
    else:
        if os.path.isfile(DISCONNECT_CONFIRM_FILE):
            os.remove(DISCONNECT_CONFIRM_FILE)
        handle_show(active)
    return 0

if __name__ == '__main__':
    sys.exit(main())
