#!/usr/bin/env python
import argparse
import subprocess
import requests
import pyperclip
from bs4 import BeautifulSoup

BUILDING = 'BUILDING'


class Bamboo:
    def __init__(self, base_url, lpass_id, private_key_file):
        self.base_url = base_url.rstrip('/')
        self.auth = self.get_auth(lpass_id)
        self.private_key_file = private_key_file

    def get_auth(self, lpass_id):
        p = subprocess.Popen(
            ['lpass', 'show', lpass_id],
            stdout=subprocess.PIPE
        )
        out, err = p.communicate()
        user = None
        password = None
        for line in out.decode('utf-8').splitlines():
            if line.startswith('Username:'):
                user = line.split()[-1]
            elif line.startswith('Password:'):
                password = line.split()[-1]
        if user and password:
            return user, password
        raise RuntimeError('Could not fetch user and pass from lastpass')

    def url(self, path):
        return self.base_url + path

    def request(self, path, **kwargs):
        return requests.get(self.url(path), auth=self.auth, **kwargs)

    def get_builds(self):
        r = self.request('/build/admin/ajax/getDashboardSummary.action')
        r.raise_for_status()
        return [
            build for build in r.json()['builds']
            if build['status'] == BUILDING
        ]

    def get_instance_endpoint(self, agent_instance_id):
        r = self.request(
            '/admin/elastic/viewElasticInstance.action',
            params={
                'instanceId': agent_instance_id,
            }
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')
        code_tags = soup.findAll('code')
        for code in code_tags:
            if code.text.startswith('ssh -i'):
                return code.text.split()[-1]

    def remove_from_known_hosts(self, host):
        host = host.split('@')[-1]
        known_hosts_file = '/home/sindri/.ssh/known_hosts'
        with open(known_hosts_file, 'r') as f:
            current = f.readlines()
        if any(host in line for line in current):
            with open(known_hosts_file, 'w') as f:
                for line in current:
                    if host not in line:
                        f.write(line)
            return True

    def ssh(self, build):
        instance_id = build['agent']['name'].split()[-1]
        print('SSH to elastic agent on %s' % (instance_id, ))
        instance_endpoint = self.get_instance_endpoint(instance_id)
        popenargs = [
            'ssh',
            '-i',
            self.private_key_file,
            instance_endpoint,
        ]
        need_yes = self.remove_from_known_hosts(instance_endpoint)
        print(' '.join(popenargs))
        pyperclip.copy(
            (need_yes and 'yes\n' or '') +
            'sudo su - bamboo\n'
            'cd bamboo-agent-home/xml-data/build-dir/%s\n' % (
                build['jobKey'],
            )
        )
        subprocess.call(popenargs)

    def build_representation(self, build):
        return ' '.join([
            build['planName'],
            '#%s' % (build['buildNumber'])
        ])

    def select_build(self, builds):
        if not builds:
            print('No builds, bye!')
            return
        elif len(builds) == 1:
            return self.ssh(builds[0])
        for i, build in enumerate(builds):
            print(i, self.build_representation(build))
        selection = input('Select:')
        if selection.isdigit():
            int_selection = int(selection)
            if int_selection >= 0 and int_selection < len(builds):
                return self.ssh(builds[int_selection])
        return self.select_build([
            build for build in builds
            if selection in self.build_representation(build)
        ])

    def main(self):
        self.select_build(self.get_builds())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--lpass-id',
        default='3916166815288712312',
    )
    parser.add_argument(
        '--base_url',
        default='https://bamboo.temposoftware.com',
    )
    parser.add_argument(
        '-i',
        default='/home/sindri/.ssh/elasticbamboo.pk',
        dest='private_key_file',
    )
    args = parser.parse_args()

    b = Bamboo(args.base_url, args.lpass_id, args.private_key_file)
    b.main()
