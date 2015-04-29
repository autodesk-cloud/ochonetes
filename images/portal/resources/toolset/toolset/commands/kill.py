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

    def __init__(self, proxy, cluster):
        super(_Automation, self).__init__()

        self.cluster = cluster
        self.killed = 0
        self.ok = 0
        self.proxy = proxy

        self.start()

    def run(self):
        try:

            #
            # - workaround to fetch the master IP and credentials as there does not seem to
            #   be a way to use 10.0.0.2 from within the pod
            #
            assert 'KUBERNETES_MASTER' in os.environ, '$KUBERNETES_MASTER not specified (check your portal pod)'
            assert 'KUBERNETES_USER' in os.environ, '$KUBERNETES_USER not specified (check your portal pod)'
            assert 'KUBERNETES_PWD' in os.environ, '$KUBERNETES_PWD not specified (check your portal pod)'

            auth = HTTPBasicAuth(os.environ['KUBERNETES_USER'], os.environ['KUBERNETES_PWD'])

            def _query(zk):
                replies = fire(zk, self.cluster, 'info')
                return len(replies), {key: hints for key, (_, hints, code) in replies.items() if code == 200}

            #
            # - each pod refers to its controller via the 'application' hint
            #
            total, js = run(self.proxy, _query)
            assert total == len(js), 'failure to communicate with one or more pods'
            for key in set([hints['application'] for hints in js.values()]):

                #
                # - HTTP DELETE the controller via the master API
                #
                url = 'https://%s/api/v1beta3/namespaces/default/replicationcontrollers/%s' % (os.environ['KUBERNETES_MASTER'], key)
                reply = requests.delete(url, auth=auth,verify=False)
                code = reply.status_code
                logger.debug('-> DELETE %s (HTTP %d)' % (url, code))
                assert code == 200 or code == 201, 'replication controller deletion failed (HTTP %d)' % code

            #
            # - the 'task' hint is the pod's identifier
            #
            for key, hints in js.items():

                #
                # - HTTP DELETE the pod via the master API
                #
                url = 'https://%s/api/v1beta3/namespaces/default/pods/%s' % (os.environ['KUBERNETES_MASTER'], hints['task'])
                reply = requests.delete(url, auth=auth,verify=False)
                code = reply.status_code
                logger.debug('-> DELETE %s (HTTP %d)' % (url, code))
                assert code == 200 or code == 201, 'pod deletion failed (HTTP %d)' % code

            self.killed = len(js)
            self.ok = 1

        except AssertionError as failure:

            logger.debug('%s : failed to deploy -> %s' % (self.cluster, failure))

        except YAMLError as failure:

            if hasattr(failure, 'problem_mark'):
                mark = failure.problem_mark
                logger.debug('%s : invalid deploy.yml (line %s, column %s)' % (self.cluster, mark.line+1, mark.column+1))

        except Exception as failure:

            logger.debug('%s : failed to deploy -> %s' % (self.cluster, diagnostic(failure)))

    def join(self, timeout=None):

        Thread.join(self)
        return self.ok, self.killed


def go():

    class _Tool(Template):

        help = \
            '''
                Deletes the replication controllers & pods for the specified cluster(s).
            '''

        tag = 'kill'

        def customize(self, parser):

            parser.add_argument('clusters', type=str, nargs='+', help='1+ clusters (can be a glob pattern, e.g foo*)')

        def body(self, args, proxy):

            #
            # - run the workflow proper (one thread per container definition)
            #
            threads = [_Automation(proxy, cluster) for cluster in args.clusters]

            #
            # - wait for all our threads to join
            #
            n = len(threads)
            outcome = [thread.join() for thread in threads]
            pct = (100 * sum(1 for ok, _ in outcome if ok)) / n if n else 0
            logger.info('%d%% success / killed %d pod(s)' % (pct, sum(killed for _, killed in outcome)))
            return 0 if pct == 100 else 1

    return _Tool()