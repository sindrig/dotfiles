if [ -d "/proc/sys/net/ipv4/conf/vpn0" -o -f "/var/run/vpnc.pid" ]; then
    echo 'VPN: up'
    echo 'VPN: up'
    echo \#00FF00
else
    echo 'VPN: down'
    echo 'VPN: down'
    echo \#FF0000
fi
