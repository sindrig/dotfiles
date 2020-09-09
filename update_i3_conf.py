#!/usr/bin/env python3
import argparse
import os

SEPARATOR = '####### END DEFAULT REGOLITH'

BANNED_BINDINGS = (
    '$mod+Shift+e',
    '$mod+Shift+b',
    '$mod+Shift+p',
    '$mod+Escape',
    '$mod+Shift+s',
    '$mod+i',
)

EXTRA_QUOTE_LINES = ('for_window [class="Gnome-control-center"]',)


def shadow_binding(binding, source_lines):
    for line in source_lines:
        parts = line.split()
        if (len(parts) > 1 and parts[1] in (binding, *BANNED_BINDINGS)) or any(
            (line.startswith(ql) for ql in EXTRA_QUOTE_LINES)
        ):
            yield f'# {line}'
        else:
            yield line


def main(source_file, target_file):
    with open(source_file, 'r') as f:
        source_lines = f.readlines()
    with open(target_file, 'r') as f:
        target_lines = []
        for line in f:
            if line.startswith(SEPARATOR):
                break
        else:
            raise RuntimeError(
                f'Expected to find {SEPARATOR} in {target_file}'
            )
        for line in f:
            target_lines.append(line)

    for target_line in target_lines:
        if target_line.startswith('bindsym'):
            binding = target_line.split()[1]
            source_lines = list(shadow_binding(binding, source_lines))
    with open(target_file, 'w') as f:
        f.writelines(source_lines + ['\n', SEPARATOR, '\n'] + target_lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'regolith_i3_file', default='/etc/regolith/i3/config', nargs='?'
    )
    args = parser.parse_args()
    file_to_update = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'config',
        'regolith',
        'i3',
        'config',
    )
    main(source_file=args.regolith_i3_file, target_file=file_to_update)
