#!/usr/bin/python3
import os
import time
import signal
import re
import datetime
import json
import sys
import subprocess
import psutil
import tempfile
import traceback

ACTIVE_REGEX = re.compile('GENERAL\.STATE:\s*activated')
VPN_NAME = 'Tempo VPN'
DISCONNECT_CONFIRM_FILE = '/tmp/vpn-confirm-file'
dateformat = '%Y%m%d%H%M%S'
CLIENT_CONF = '/etc/openvpn/client/tempo.conf'


def get_disconnect_date():
    if os.path.isfile(DISCONNECT_CONFIRM_FILE):
        with open(DISCONNECT_CONFIRM_FILE, 'r') as f:
            return datetime.datetime.strptime(f.read(), dateformat)


def set_disconnect_date(date):
    with open(DISCONNECT_CONFIRM_FILE, 'w') as f:
        f.write(date.strftime(dateformat))


def sudo(args):
    return subprocess.Popen(
        ['sudo', '-A'] + args,
        # stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={'SUDO_ASKPASS': '/usr/bin/x11-ssh-askpass', 'DISPLAY': ':0'},
    )


def updown_vpn(active):
    try:
        if active:
            es = []
            for proc in openvpn_processes():
                p = sudo(
                    [
                        '/home/sindri/bin/killvpn.sh',
                        '-%s' % (signal.SIGKILL.value),
                    ]
                )
                o, e = p.communicate()
                if e:
                    es.append(e.decode('utf-8'))
            if es and is_active():
                raise ValueError(''.join(es))
        else:
            auth = get_auth()
            with tempfile.NamedTemporaryFile(mode='w') as temp:
                temp.write(auth)
                temp.flush()
                # p = sudo([
                #     '/usr/bin/openvpn',
                #     '--daemon', 'tempovpn',
                #     '--config', CLIENT_CONF,
                #     '--log', '/tmp/vpnlog.log',
                #     '--auth-user-pass',
                #     temp.name,
                # ])
                p = subprocess.run(
                    [
                        'xfce4-terminal',
                        '--hold',
                        '-e',
                        ' '.join(
                            [
                                'sudo',
                                '/usr/bin/openvpn',
                                '--config',
                                CLIENT_CONF,
                                '--auth-user-pass',
                                temp.name,
                            ]
                        ),
                    ],
                    capture_output=True,
                )
                o = p.stdout
                e = p.stderr
                time.sleep(1)
        if e:
            raise ValueError(e)
        logfile = os.path.join(os.path.dirname(__file__), 'vpn_log')
        with open(logfile, 'w+b') as f:
            f.write(o)
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


def get_auth():
    env = os.environ.copy()
    env['DISPLAY'] = ':0'
    p = subprocess.Popen(
        ['lpass', 'show', '-j', 'onelogin.com'],
        # stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    o, e = p.communicate()
    if e:
        raise ValueError(e)
    data = json.loads(o)
    item = data[0]
    return '%s\n%s' % (item['username'], item['password'],)


def openvpn_processes():
    for proc in psutil.process_iter(attrs=['name', 'pid']):
        if proc.name() == 'openvpn' and CLIENT_CONF in proc.cmdline():
            yield proc


def is_active():
    return any(openvpn_processes())


def main():
    active = is_active()
    if os.environ.get('BLOCK_BUTTON'):
        handle_click(active, int(os.environ['BLOCK_BUTTON']))
    else:
        handle_show(active)
    return 0


if __name__ == '__main__':
    sys.exit(main())
