#!/usr/bin/env python3
from __future__ import print_function
import filecmp
import glob
import os
import shutil


def main():
    to_create = gather_symlinks('*')
    if input('Would you like to continue? (y/n)') in 'yY':
        create_symlinks(to_create)

NON_HIDDEN_FOLDERS = [
    'bin'
]


def get_destination(src):
    hidden = True
    for fldr in NON_HIDDEN_FOLDERS:
        if src.startswith(fldr):
            hidden = False
    return '{}/{}{}'.format(
        os.path.expanduser('~'),
        '.' if hidden else '',
        src
    )


def gather_symlinks(fldr):
    symlinks = []
    for src in glob.glob(os.path.join(fldr, '*')):
        if os.path.isdir(src):
            symlinks += gather_symlinks(src)
        else:
            destination = get_destination(src)
            if os.path.exists(destination) and not os.path.islink(destination):
                if filecmp.cmp(src, destination):
                    print(
                        (
                            'Files {src} and {destination} are identical. '
                            'Will be saving {destination} as {destination}.bak'
                        ).format(src=src, destination=destination)
                    )
                else:
                    raise ValueError(
                        (
                            'File {} already exists and differs from '
                            'the one in {}'
                        ).format(destination, src)
                    )
            elif os.path.islink(destination):
                if os.path.realpath(destination) != os.path.abspath(src):
                    raise ValueError(
                        (
                            'Current symlink {destination} points to {cur} '
                            'at the moment and I don\'t wanna fuck things'
                            'up'
                        ).format(
                            destination=destination,
                            cur=os.path.realpath(destination)
                        )
                    )
            print('{}->{}'.format(src, destination))
            symlinks.append((os.path.abspath(src), destination))
    return symlinks


def create_symlinks(symlinks):
    for src, destination in symlinks:
        fldr = os.path.dirname(destination)
        if not os.path.isdir(fldr):
            os.makedirs(fldr)
        if not os.path.islink(destination):
            if (
                os.path.exists(destination) and
                os.path.isfile(destination)
            ):
                shutil.move(destination, '{}.bak'.format(destination))
            os.symlink(src, destination)


if __name__ == '__main__':
    main()
