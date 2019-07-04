#!/usr/bin/env python
import argparse
import json
import itertools
import os
import datetime
import requests
import shutil
import time
from threading import Lock
from multiprocessing.pool import ThreadPool

from urllib.parse import parse_qs, urlparse

URL_TEMPLATE = (
    'http://smooth.ruv.cache.is/{openclose}/{date}/2400kbps/{fn}.mp4'
)
DATE_FORMAT = '%Y/%m/%d'
DATE_PART_LENGTH = 4 + 1 + 2 + 1 + 2
CACHE_LOCATION = os.path.join(os.path.expanduser('~'), '.ruvdlcache')
DEFAULT_VIDEO_DESTINATION = os.path.join(os.path.expanduser('~'), 'Videos/ruv')


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
    def __init__(self, fn, url, date, etag):
        self.fn = fn
        self.url = url
        self.date = date
        self.etag = etag

    def to_dict(self):
        return {
            'fn': self.fn,
            'url': self.url,
            'date': self.date.strftime(DATE_FORMAT),
            'etag': self.etag,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            fn=data['fn'],
            url=data['url'],
            date=datetime.datetime.strptime(data['date'], DATE_FORMAT),
            etag=data['etag'],
        )

    def set_target_path(self, path):
        self.target_path = path

    def __hash__(self):
        return hash(self.etag)
        # return hash((self.fn, self.url, self.date, self.etag))

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

    def get_entry(self, date, fn):
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
                self.cache.set(
                    cache_key,
                    {'url': r.url, 'etag': r.headers['ETag']}
                )
            else:
                self.cache.set(cache_key, False)
        info = self.cache.get(cache_key)
        if info:
            return Entry(
                fn=fn,
                url=info['url'],
                date=date,
                etag=info['etag'],
            )

    def get_new_fn(self, fn, direction):
        fn_id, something = fn.split('T')
        new_id = str(int(fn_id) + direction)
        while len(new_id) < len(fn_id):
            new_id = f'0{new_id}'
        return f'{new_id}T{something}'

    def crawl(self, date, fn, direction=1):
        new_fn = self.get_new_fn(fn, direction)
        for i in range(self.itercount):
            # Search for maximum 2 weeks back in time
            date_to_check = (
                date +
                datetime.timedelta(
                    days=i * direction * self.days_between_episodes
                )
            )
            entry = self.get_entry(
                date_to_check,
                new_fn,
            )
            if entry:
                yield entry
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
            first_exists = self.get_entry(date, fn)
            if not first_exists:
                raise RuntimeError('Could not get url for first episode...?')
            # files.add(Entry(fn, episode_url))
            print('Searching backwards in time...')
            for entry in self.crawl(date, fn, direction=-1):
                files.add(entry)
            print('Searching forward in time...')
            for entry in self.crawl(date, fn, direction=1):
                files.add(entry)
        self.cache.write()
        return files


class Downloader:
    def __init__(self, destination, program, episode_entries, threaded=True):
        self.destination = destination
        self.program = program
        self.episode_entries = episode_entries
        self.threaded = threaded

    def organize(self):
        info_fn = os.path.join(
            self.destination,
            self.program['title'],
            'program_info.json'
        )
        os.makedirs(os.path.dirname(info_fn), exist_ok=True)
        try:
            with open(info_fn, 'r') as f:
                seasons = {
                    season: {Entry.from_dict(entry) for entry in entries}
                    for season, entries in json.loads(f.read()).items()
                }
        except FileNotFoundError:
            seasons = {}
        # seasons = {
        #     1: {entry, entry, entry},
        #     2: {entry, entry, entry},
        # }
        # Sort episodes into seasons
        for entry in sorted(
            self.episode_entries,
            key=lambda entry: entry.date
        ):
            for season in seasons.keys():
                if any(
                    abs((e.date - entry.date).days) < 10
                    for e in seasons[season]
                ):
                    seasons[season].add(entry)
                    break
            else:
                seasons[max((seasons or {0: 0}).keys()) + 1] = {entry}
        # Calculate target paths for entries
        for season, entries in seasons.items():
            season_folder = os.path.join(
                self.destination,
                self.program['title'],
                f'Season {season}',
            )
            os.makedirs(season_folder, exist_ok=True)
            for i, entry in enumerate(
                sorted(entries, key=lambda entry: entry.date)
            ):
                fn = (
                    f'{self.program["title"]} - '
                    f'S{str(season).zfill(2)}E{str(i + 1).zfill(2)}.mp4'
                )
                target_path = os.path.join(
                    season_folder,
                    fn,
                )
                entry.set_target_path(target_path)
        # Finally, make sure we don't have the same etag multiple times,
        # prefer the first one in chronological order
        found_etags = []
        for season, entries in seasons.items():
            for entry in [
                entry for entry in entries if entry.etag in found_etags
            ]:
                entries.remove(entry)
            found_etags += [entry.etag for entry in entries]
        with open(info_fn, 'w') as f:
            serialized_seasons = {
                season: [entry.to_dict() for entry in entries]
                for season, entries in seasons.items()
            }
            f.write(json.dumps(serialized_seasons, indent=4))
        return list(itertools.chain(*seasons.values()))

    def download_file(self, entry):
        if os.path.exists(entry.target_path):
            print(
                f'Skipping {entry.target_path} - {entry.url} because '
                'it already exists.'
            )
            return False
        else:
            print(f'Downloading {entry.url} to {entry.target_path}')
        r = requests.get(entry.url, stream=True)

        if r.ok:
            start = time.time()
            total_length = int(r.headers.get('content-length'))
            dl = 0
            perc_done = 0
            with open(entry.target_path, 'wb') as f:
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

            size = int(os.path.getsize(entry.target_path) / 1024**2)
            print(
                f'{entry.target_path} ({size}MB) '
                f'downloaded in {int(time.time() - start)}s!'
            )
            return True
        print(f'Error {r.status_code} for {entry.url}')
        return False

    def start(self):
        print('Organizing...')
        entries = self.organize()
        print(f'Downloading {len(entries)} files')
        if self.threaded:
            results = ThreadPool(8).imap_unordered(
                self.download_file,
                entries,
            )
        else:
            results = [
                self.download_file(entry) for entry in entries
            ]
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


def main(args):
    program_id = get_program_id(args.query)
    r = requests.get(
        f'https://api.ruv.is/api/programs/program/{program_id}/all'
    )
    r.raise_for_status()
    program = r.json()
    crawler = Crawler(
        days_between_episodes=args.days_between_episodes,
        iteration_count=args.iteration_count,
        program=program,
    )
    episode_entries = crawler.search_for_episodes()
    downloader = Downloader(
        destination=args.destination,
        program=program,
        episode_entries=episode_entries,
        threaded=not args.sequential,
    )
    downloader.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'query',
        help='Search term to search for programs.'
    )
    parser.add_argument(
        'destination', default=DEFAULT_VIDEO_DESTINATION, nargs='?',
        type=os.path.abspath,
        help='Top level destination directory.'
    )
    parser.add_argument(
        '--days-between-episodes', type=int, default=7, nargs='?',
        help='Rate of episode release.'
    )
    parser.add_argument(
        '--iteration-count', type=int, default=5, nargs='?',
        help='Maximum days to allow for now shows found.'
    )
    parser.add_argument(
        '--empty-cache',
        action='store_true',
        help='Empty request cache to api.ruv.is before running.'
    )
    parser.add_argument(
        '--sequential',
        action='store_true',
        help='Do not run threaded, only download one file at a time.'
    )
    args = parser.parse_args()
    if args.empty_cache:
        if os.path.exists(CACHE_LOCATION):
            shutil.rmtree(CACHE_LOCATION)
    os.makedirs(args.destination, exist_ok=True)
    os.makedirs(CACHE_LOCATION, exist_ok=True)
    main(args)
