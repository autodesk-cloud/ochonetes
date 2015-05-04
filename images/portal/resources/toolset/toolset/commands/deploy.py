#
# Copyright (c) 2015 Autodesk Inc.
# All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import datetime
import json
import logging
import os
import requests
import time
import yaml

from ochopod.core.fsm import diagnostic, shutdown
from ochopod.core.utils import merge, retry, shell
from requests.auth import HTTPBasicAuth
from threading import Thread
from toolset.io import fire, run
from toolset.tool import Template
from yaml import YAMLError

#: Our ochopod logger.
logger = logging.getLogger('ochopod')


class _Automation(Thread):

    def __init__(self, proxy, template, namespace, pods):
        super(_Automation, self).__init__()

        self.deployed = 0
        self.namespace = namespace
        self.ok = 0
        self.pods = pods
        self.proxy = proxy
        self.template = template

        self.start()

    def run(self):
        try:

            #
            # - workaround to fetch the master IP and credentials as there does not seem to
            #   be a way to use 10.0.0.2 from within the pod
            #
            assert 'KUBERNETES_MASTER' in os.environ,   '$KUBERNETES_MASTER not specified (check your portal pod)'
            assert 'KUBERNETES_USER' in os.environ,     '$KUBERNETES_USER not specified (check your portal pod)'
            assert 'KUBERNETES_PWD' in os.environ,      '$KUBERNETES_PWD not specified (check your portal pod)'

            auth = HTTPBasicAuth(os.environ['KUBERNETES_USER'], os.environ['KUBERNETES_PWD'])

            with open(self.template, 'r') as f:

                #
                # - parse the yaml file
                # - add the ochopod control port if not specified
                #
                cfg = yaml.load(f)
                if 8080 not in cfg['ports']:
                    cfg['ports'].append(8080)

                #
                # -
                #
                suffix = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
                qualified = 'ochopod.%s.%s-%s' % (self.namespace, cfg['cluster'], suffix)

                env = \
                    {
                        'KUBERNETES_MASTER': os.environ['KUBERNETES_MASTER'],
                        'KUBERNETES_USER': os.environ['KUBERNETES_USER'],
                        'KUBERNETES_PWD': os.environ['KUBERNETES_PWD'],
                        'ochopod_cluster': cfg['cluster'],
                        'ochopod_namespace': self.namespace,
                        'ochopod_application': qualified,
                        'pod': json.dumps(cfg['settings']) if 'settings' in cfg else '{}'
                    }

                labels = \
                    {
                        'name': qualified
                    }

                container = \
                    {
                        'name': cfg['cluster'],
                        'image': cfg['image'],
                        'env': [{'name': key, 'value': value} for key, value in env.items()],
                        'ports': [{'containerPort': port} for port in cfg['ports']]
                    }

                controller = \
                    {
                        'kind': 'ReplicationController',
                        'apiVersion': 'v1beta3',
                        'metadata': {'name': qualified},
                        'spec':
                            {
                                'replicas': self.pods,
                                'selector': {'name': qualified},
                                'template':
                                    {
                                        'metadata': {'labels': labels},
                                        'spec':
                                            {
                                                'containers': [container]
                                            }
                                    }
                            }

                    }

                #
                # -
                #
                headers = \
                    {
                        'content-type': 'application/json',
                        'accept': 'application/json'
                    }

                url = 'https://%s/api/v1beta3/namespaces/default/replicationcontrollers' % os.environ['KUBERNETES_MASTER']
                reply = requests.post(url, auth=auth, data=json.dumps(controller), headers=headers, verify=False)
                code = reply.status_code
                logger.debug('-> POST %s (HTTP %d)' % (url, code))
                assert code == 200 or code == 201, 'submission failed (HTTP %d)' % code

            self.deployed = self.pods
            self.ok = 1

        except AssertionError as failure:

            logger.debug('%s : failed to deploy -> %s' % (self.template, failure))

        except YAMLError as failure:

            if hasattr(failure, 'problem_mark'):
                mark = failure.problem_mark
                logger.debug('%s : invalid deploy.yml (line %s, column %s)' % (self.template, mark.line+1, mark.column+1))

        except Exception as failure:

            logger.debug('%s : failed to deploy -> %s' % (self.template, diagnostic(failure)))

    def join(self, timeout=None):

        Thread.join(self)
        return self.ok, self.deployed


def go():

    class _Tool(Template):

        help = \
            '''
                Spawns a replication controller for each of the specified cluster(s).
            '''

        tag = 'deploy'

        def customize(self, parser):

            parser.add_argument('containers', type=str, nargs='*', default='*', help='1+ container definitions (can be a glob pattern, e.g foo*)')
            parser.add_argument('-n', '--namespace', action='store', dest='namespace', type=str, default='default', help='cluster namespace')
            parser.add_argument('-o', '--overrides', action='store', dest='overrides', type=str, help='overrides yaml file')
            parser.add_argument('-p', '--pods', action='store', dest='pods', default=1, type=int, help='pod capacity')

        def body(self, args, proxy):

            assert len(args.containers), 'at least one container definition is required'

            #
            # - run the workflow proper (one thread per container definition)
            #
            threads = [_Automation(proxy, yml, args.namespace, args.pods) for yml in args.containers]

            #
            # - wait for all our threads to join
            #
            n = len(threads)
            outcome = [thread.join() for thread in threads]
            pct = (100 * sum(1 for ok, _ in outcome if ok)) / n if n else 0
            logger.info('%d%% success / spawned %d pod(s)' % (pct, sum(deployed for _, deployed in outcome)))
            return 0 if pct == 100 else 1

    return _Tool()