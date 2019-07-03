#!/usr/bin/env python
import argparse
import json
import os
import datetime
import requests
import shutil
import time
from multiprocessing.pool import ThreadPool

from urllib.parse import parse_qs, urlparse

URL_TEMPLATE = (
    'http://smooth.ruv.cache.is/{openclose}/{date}/2400kbps/{fn}.mp4'
)
DATE_FORMAT = '%Y/%m/%d'
DATE_PART_LENGTH = 4 + 1 + 2 + 1 + 2
CACHE_LOCATION = os.path.join(os.path.expanduser('~'), '.ruvdlcache')


class DiskCache:
    def __init__(self, program_id):
        self.location = os.path.join(CACHE_LOCATION, f'{program_id}.json')
        try:
            with open(self.location, 'r') as f:
                self._data = json.loads(f.read())
        except FileNotFoundError:
            self._data = {}

    def get(self, key):
        return self._data[key]

    def set(self, key, data):
        self._data[key] = data

    def has(self, key):
        return key in self._data

    def write(self):
        with open(self.location, 'w') as f:
            f.write(json.dumps(self._data))


class Entry:
    def __init__(self, fn, url):
        self.fn = fn
        self.url = url

    def __hash__(self):
        return hash((self.fn, self.url))

    def __eq__(self, other):
        return isinstance(other, Entry) and hash(self) == hash(other)


class Crawler:
    def __init__(
        self, program, iteration_count, days_between_episodes
    ):
        self.program = program
        self.itercount = iteration_count
        self.days_between_episodes = days_between_episodes
        self.prefer_open = True
        self.cache = DiskCache(program['id'])
        print(
            '\n'.join([
                'Initializing crawler with:',
                f'Iteration count: {self.itercount}',
                f'Days between episodes: {self.days_between_episodes}',
            ])
        )

    def check_exists_and_get_url(self, date, fn):
        cache_key = f'{date.strftime(DATE_FORMAT)}-{fn}'
        if not self.cache.has(cache_key):
            r = requests.head(
                URL_TEMPLATE.format(
                    date=date.strftime(DATE_FORMAT),
                    fn=fn,
                    openclose='opid' if self.prefer_open else 'lokad',
                )
            )
            print(
                'Checking %s - %s - %s (is_open: %s)' % (
                    date.strftime(DATE_FORMAT),
                    fn,
                    r.ok,
                    self.prefer_open,
                )
            )
            if r.ok:
                self.cache.set(cache_key, r.url)
            else:
                self.cache.set(cache_key, False)
        return self.cache.get(cache_key)

    def get_new_fn(self, fn, direction):
        fn_id, something = fn.split('T')
        new_id = str(int(fn_id) + direction)
        while len(new_id) < len(fn_id):
            new_id = f'0{new_id}'
        return f'{new_id}T{something}'

    def crawl(self, date, fn, direction=1):
        new_fn = self.get_new_fn(fn, direction)
        for i in range(1, self.itercount):
            # Search for maximum 2 weeks back in time
            date_to_check = (
                date +
                datetime.timedelta(
                    days=i * direction * self.days_between_episodes
                )
            )
            episode_url = self.check_exists_and_get_url(date_to_check, new_fn)
            if episode_url:
                yield Entry(new_fn, episode_url)
                yield from self.crawl(date_to_check, new_fn, direction)
                break

    def search_for_episodes(self):
        files = set()
        episodes = self.program['episodes']
        if not episodes:
            raise RuntimeError('No episodes found...')
        for episode in episodes:
            self.prefer_open = 'opid' in episode['file']
            manifest_url = episode['file']
            parts = urlparse(manifest_url)
            query = parse_qs(parts.query)
            # query['streams'] = (
            #     '2019/06/30/2400kbps/5019197T0.mp4.m3u8:2400,2019/06/30/500kbps/'
            #     '5019197T0.mp4.m3u8:500,2019/06/30/800kbps/5019197T0.mp4.m3u8:800'
            #     ',2019/06/30/1200kbps/5019197T0.mp4.m3u8:1200,2019/06/30/3600kbps'
            #     '/5019197T0.mp4.m3u8:3600'
            # )
            wanted_stream = query['streams'][0].split(',')[0]
            # Dates are the first part, '%Y/%m/%d'
            date = datetime.datetime.strptime(
                wanted_stream[:DATE_PART_LENGTH],
                DATE_FORMAT,
            )
            fn = wanted_stream.split('/')[-1].split('.')[0]
            episode_url = self.check_exists_and_get_url(date, fn)
            if not episode_url:
                raise RuntimeError('Could not get url for first episode...?')
            files.add(Entry(fn, episode_url))
            print('Searching backwards in time...')
            for entry in self.crawl(date, fn, direction=-1):
                files.add(entry)
            print('Searching forward in time...')
            for entry in self.crawl(date, fn, direction=1):
                files.add(entry)
        self.cache.write()
        return files


class Downloader:
    def __init__(self, destination, files):
        self.destination = destination
        self.files = files

    def download_file(self, entry):
        path = os.path.join(self.destination, f'{entry.fn}.mp4')
        if os.path.exists(path):
            print(f'Skipping {entry.fn} - {entry.url}. {path} already exists.')
            return False
        else:
            print(f'Downloading {entry.url} to {path}')
        r = requests.get(entry.url, stream=True)

        if r.ok:
            start = time.time()
            total_length = int(r.headers.get('content-length'))
            dl = 0
            perc_done = 0
            with open(path, 'wb') as f:
                for chunk in r:
                    dl += len(chunk)
                    current = int(dl * 10 / total_length)
                    if current > perc_done:
                        perc_done = current
                        print(
                            f'{entry.fn} {perc_done * 10}% '
                            f'({int(dl//(time.time() - start)/1024)}kbps)'
                        )
                    f.write(chunk)

            size = int(os.path.getsize(path) / 1024**2)
            print(
                f'{path} ({size}MB) downloaded in {int(time.time() - start)}s!'
            )
            return True
        print(f'Error {r.status_code} for {entry.url}')
        return False

    def start(self):
        print(f'Downloading {len(self.files)} files')
        results = ThreadPool(8).imap_unordered(
            self.download_file,
            self.files,
        )
        print(f'{len([r for r in results if r])} files downloaded')


def get_program_id(query):
    r = requests.get(
        f'https://api.ruv.is/api/programs/search/tv/{query}'
    )
    r.raise_for_status()
    programs = r.json()['programs']
    if not programs:
        raise RuntimeError(f'No programs found matching {query}')
    while True:
        for i, program in enumerate(programs):
            print(i + 1, ':', program['title'])
        selection = input('Select program: ')
        if selection.isdigit():
            selection = int(selection)
            if selection > 0 and selection <= len(programs):
                return programs[selection - 1]['id']


def main(query, destination, days_between_episodes, iteration_count):
    program_id = get_program_id(query)
    r = requests.get(
        f'https://api.ruv.is/api/programs/program/{program_id}/all'
    )
    r.raise_for_status()
    program = r.json()
    crawler = Crawler(
        days_between_episodes=days_between_episodes,
        iteration_count=iteration_count,
        program=program,
    )
    all_files = crawler.search_for_episodes()
    downloader = Downloader(destination, all_files)
    downloader.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('destination')
    parser.add_argument(
        '--days-between-episodes', type=int, default=7, nargs='?'
    )
    parser.add_argument(
        '--iteration-count', type=int, default=5, nargs='?'
    )
    parser.add_argument('--empty-cache', action='store_true')
    args = parser.parse_args()
    if args.empty_cache:
        if os.path.exists(CACHE_LOCATION):
            shutil.rmtree(CACHE_LOCATION)
    destination = os.path.abspath(args.destination)
    if not os.path.isdir(os.path.dirname(destination)):
        raise RuntimeError(f'Parent directory of {destination} does not exist')
    os.makedirs(destination, exist_ok=True)
    os.makedirs(CACHE_LOCATION, exist_ok=True)
    main(
        args.query,
        destination,
        args.days_between_episodes,
        args.iteration_count,
    )
