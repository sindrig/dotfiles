#!/usr/bin/env python

import argparse
import pulsectl
import sys

pulse = pulsectl.Pulse('pulse-hs-profile-stuff')

HSP = 'headset_head_unit'
A2DP = 'a2dp_sink'


def change_profile(card, profile):
    pulse.card_profile_set(card, profile)


def move_all_sink_inputs_to_card(card):
    for sink in pulse.sink_list():
        if sink.card == card.index:
            card_sink = sink
            break
    else:
        print(f'No sink found for card index {card.index}')
        sys.exit(158)
    for sink_input in pulse.sink_input_list():
        if sink_input.sink != card_sink.index:
            pulse.sink_input_move(sink_input.index, card_sink.index)


def get_card():
    available_cards = []
    for card in pulse.card_list():
        if card.name.startswith('bluez_card'):
            available_cards.append(card)
    if not available_cards:
        print('No bluez cards found, exiting')
        sys.exit(157)
    elif len(available_cards) > 1:
        print('Multiple cards found, please select:')
        for i, card in enumerate(available_cards):
            print(f'\t{i+1}: {card.name} [{card.description}]')
        selection = None
        while 1:
            selection = input()
            if selection.isdigit():
                selection = int(selection)
                if 0 < selection <= len(available_cards):
                    return available_cards[selection - 1]
            print('Invalid input...')
    else:
        return available_cards[0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'profile',
        choices=['auto', 'mic', 'audio'],
        default='auto',
        nargs='?',
    )
    args = parser.parse_args()
    card = get_card()
    if args.profile == 'auto':
        if card.profile_active.name == A2DP:
            profile = HSP
        else:
            profile = A2DP
    elif args.profile == 'mic':
        profile = HSP
    elif args.profile == 'audio':
        profile = A2DP
    change_profile(card, profile)
    move_all_sink_inputs_to_card(card)
    print(f'Activated profile {profile}')
