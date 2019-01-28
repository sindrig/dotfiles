#!/usr/bin/env python

import argparse
import pulsectl

pulse = pulsectl.Pulse('pulse-volume-stuff')

VOL_PERCENT = .05


def get_active_sinks():
    for sink in pulse.sink_list():
        if sink.state == 'running':
            yield sink


def up(sink):
    volume = sink.volume
    volume.value_flat += VOL_PERCENT
    if volume.value_flat > 1:
        volume.value_flat = 1
    pulse.volume_set(sink, volume)


def down(sink):
    volume = sink.volume
    volume.value_flat -= VOL_PERCENT
    if volume.value_flat < 0:
        volume.value_flat = 0
    pulse.volume_set(sink, volume)


def toggle_mute(sink):
    pulse.mute(sink, not sink.mute)
    return sink.mute and 'Muted'


ACTIONS = {
    'up': up,
    'down': down,
    'mute': toggle_mute,
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'action',
        choices=['up', 'down', 'mute', 'show'],
        default='show',
        nargs='?',
    )
    args = parser.parse_args()
    action = ACTIONS.get(args.action, lambda sink: None)

    for sink in get_active_sinks():
        result = action(sink)
        if result:
            print(result)
        else:
            print(f'{int(round(sink.volume.value_flat * 100))}%')
