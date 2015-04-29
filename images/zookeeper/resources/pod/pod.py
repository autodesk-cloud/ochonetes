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
import logging

from jinja2 import Environment, FileSystemLoader, Template
from ochopod.bindings.ec2.kubernetes import Pod
from ochopod.models.piped import Actor as Piped
from ochopod.models.reactive import Actor as Reactive
from os.path import join, dirname

logger = logging.getLogger('ochopod')


if __name__ == '__main__':

    class Model(Reactive):

        damper = 10.0

        sequential = True

    class Strategy(Piped):

        cwd = '/opt/zookeeper-3.4.6'

        strict = True

        def configure(self, cluster):

            #
            # - assign the server/id bindings to enable clustering
            # - lookup the port mappings for each pod (TCP 2888 and 3888)
            #
            peers = {}
            local = cluster.index + 1
            for n, key in enumerate(sorted(cluster.pods.keys()), 1):
                pod = cluster.pods[key]
                suffix = '%d:%d' % (pod['ports']['2888'], pod['ports']['3888'])
                peers[n] = '%s:%s' % (pod['ip'], suffix)

            # - set "this" node as 0.0.0.0:2888:3888
            # - i've observed weird behavior with docker 1.3 where zk can't bind the address if specified
            #
            peers[local] = '0.0.0.0:2888:3888'
            logger.debug('local id #%d, peer configuration ->\n%s' %
                         (local, '\n'.join(['\t#%d\t-> %s' % (n, mapping) for n, mapping in peers.items()])))

            #
            # - set our server index
            #
            template = Template('{{id}}')
            with open('/var/lib/zookeeper/myid', 'wb') as f:
                f.write(template.render(id=local))

            #
            # - render the zk config template with our peer bindings
            #
            env = Environment(loader=FileSystemLoader(join(dirname(__file__), 'templates')))
            template = env.get_template('zoo.cfg')
            mapping = \
                {
                    'peers': peers
                }

            with open('%s/conf/zoo.cfg' % self.cwd, 'wb') as f:
                f.write(template.render(mapping))

            return 'bin/zkServer.sh start-foreground', {}

    Pod().boot(Strategy, model=Model)