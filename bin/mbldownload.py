#!/usr/bin/env python
import asyncio
import urllib.request
import argparse
import re
import os
import shutil

from unidecode import unidecode

BASE_DIR = os.path.join(os.path.expanduser('~'), 'Images', 'mbldownload')

photourlfinder = re.compile(r'(https://www.mbl.is/fasteignir/fasteign/\d+)')
title_finder = re.compile(r'<meta property="og:title" content="(.*)" \/>')
img_finder = re.compile(r'<img src="(https://cdn.mbl.is[^"]+)"')
non_valid_fn_chars = re.compile(r'\W')


async def download(url):
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    return {
        'url': url,
        'response': response.read()
    }


def get_photo_url_or_die(url):
    groups = photourlfinder.findall(url)
    if len(groups) != 1:
        raise argparse.ArgumentParser(
            'Wrong format for url. Example: '
            'https://www.mbl.is/fasteignir/fasteign/863252/'
        )
    return f'{groups[0]}/photos/'


async def main(url, force=False):
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    url = get_photo_url_or_die(url)
    html = (await download(url))['response'].decode('utf8')
    original_title = title_finder.findall(html)[0]
    safe_title = non_valid_fn_chars.sub('', unidecode(original_title))
    target_dir = os.path.join(BASE_DIR, safe_title)
    if os.path.exists(target_dir):
        if force:
            print('Path exists, forcing delete because --force')
            shutil.rmtree(target_dir)
        else:
            raise RuntimeError(f'{target_dir} exists, aborting.')
    os.makedirs(target_dir)
    image_downloads = await asyncio.gather(
        *[download(img) for img in img_finder.findall(html)]
    )
    with open(os.path.join(target_dir, 'index.html'), 'w') as index_file:
        index_file.write('<html>')
        index_file.write(f'<head><title>{original_title}</title></head>')
        index_file.write('<body>')
        for i, result in enumerate(image_downloads):
            contents = result['response']
            extension = os.path.splitext(result['url'])[1]
            fn = f'{i+1}{extension}'
            with open(os.path.join(target_dir, fn), 'wb') as f:
                f.write(contents)
            index_file.write(f'<img src="{fn}" />')

        index_file.write('</body>')
        index_file.write('</html>')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.url, args.force))
