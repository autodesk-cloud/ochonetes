## Ochonetes

### Overview

This project is a small development PaaS leveraging [**Ochopod**](https://github.com/autodesk-cloud/ochopod)
and overlaying it on top of [**Kubernetes**](https://github.com/GoogleCloudPlatform/kubernetes).

It provides a self-contained web-shell ([**JQuery**](https://jquery.com/) rocks !) hosting our little toolkit that will
allow you to create, query and manage your ochopod containers. It also lets you CURL your commands directly which is
a great way to build your CI/CD pipeline !

Please note we **only support bindings to run over AWS** at this point. This project was tested with **release 0.16**.

Please also note the rather clunky setup involving the admin password and master IP will be cleaned up as soon as I
can get my hand on [**pull request 7101**](https://github.com/GoogleCloudPlatform/kubernetes/pull/7101) and fold in the
concept of _service account_.

### Getting started

#### Step 1 : install K8S on AWS

You know how to do it. Just peruse their [**AWS guide**](https://github.com/GoogleCloudPlatform/kubernetes/blob/master/docs/getting-started-guides/aws.md)
that will get you setup in minutes.

Note what the master IP is and what your credentials. These can be found locally at the bottom of the ```config``` file
that the installer created:

```
$ cat ~/.kube/config
```

#### Step 2 : deploy our proxy

We use a simple proxy mechanism to interact with our containers which is deployed as a pod. To create the pod use the included create-ocho-proxy script:

```
$ ./create-ocho-proxy ~/workspace/kubernetes 52.11.127.120 admin d8f7d9s8f7sd9
```

The _create_ will return immediately. Wait a bit until the pod is up and note the public IP it is running from. You
can check the state of your pods at any time by doing:

```
$ kubernetes/cluster/kubectl.sh get pods
```

Look for _ocho-proxy_ and note its internal EC2 IP address (usually something like ```ip-172-20-0-11.ec2.internal```).
Go in your AWS EC2 console and find out what minion matches it. What you want of course it the minion public IP (e.g
the one you can reach from your workstation).

This IP (or the corresponding hostname, whatever you prefer) will be the only thing you need to access from now on.
You can easily firewall it depending on your needs. Simply use your browser and look the proxy node IP up on port 9000.
You should see our little web-shell (notice the elegant ascii art).

### The CLI

You are now all setup and can remotely issue commands to the proxy. Are you afraid of using CURL or feel lazy ? No
problemo, use our little self-contained CLI ! You just need to have [**Python 2.7+**](https://www.python.org/)
installed locally:

```
$ chmod +x cli.py
$ ./cli.py <PROXY IP>
welcome to the ocho CLI ! (CTRL-C to exit)
>
```

You can set the $OCHOPOD_PROXY environment variable to avoid passing the proxy IP on the command line. Any command
typed in that interactive session will be relayed to your proxy ! If you prefer to CURL directory you can do so as
well.

The proxy supports a whole set of tools doing various things. Just type ```help``` in the CLI to get a list of what is
there. Each tool also has supports a ```---help``` switch that will print out all the details you need to know. As
an example:

```
$ ./cli.py
welcome to the ocho CLI ! (CTRL-C to exit)
> help
available commands -> deploy, grep, info, kill, log, ls, off, on

> grep --help
usage: ocho grep [-h] [-d] [clusters [clusters ...]]

Displays high-level information for the specified cluster(s).

positional arguments:
  clusters     1+ clusters (can be a glob pattern, e.g foo*)

optional arguments:
  -h, --help   show this help message and exit
  -d, --debug  debug mode
```

### Deploying your first containers

Go ahead and use the CLI to deploy a 3 node [**Zookeeper**](https://zookeeper.apache.org/) ensemble ! Look at the
little ```zookeeper.yml```. This is the container definition you are going to send to the proxy for deployment.
The proxy will then setup the corresponding k8s infrastructure (replication controller & pods) for you and ochopod will
automatically cluster those pods into a functional cross-configured ensemble. If you are a nerd please have a look at
```images/zookeeper``` to see what is hiding in our image.

Let us get going with the CLI:

```
> deploy zookeeper.yml -p 3
100% success / spawned 3 pod(s)
```

This is it ! Your ensemble is now booting. Wait a bit for the cluster to settle (please keep in mind your minions
will have to pull the image from the hub upon the very first run, this can take up to a minute) and poof you will have
a nice ensemble you can access at TCP 2181 !

```
> grep

<*> -> 100% replies (4 pods total) ->

cluster                |  pod IP       |  process  |  state
                       |               |           |
default.ocho-proxy #0  |  10.244.1.5   |  running  |  leader
default.zookeeper #0   |  10.244.1.30  |  running  |  leader
default.zookeeper #1   |  10.244.1.31  |  running  |  follower
default.zookeeper #2   |  10.244.2.12  |  running  |  follower
```

### Documentation

You can [**peruse our online documentation**](http://autodesk-cloud.github.io/ochonetes/) for examples, design notes
and more !

The [**Sphinx**](http://sphinx-doc.org/) materials can be found under docs/. Just go in there and build for your
favorite target, for instance:

```
$ cd docs
$ make html
```

The docs will be written to _docs/_build/html_. This is all Sphinx based and you have many options and knobs to
tweak should you want to customize the output.

### Support

Contact autodesk.cloud.opensource@autodesk.com for more information about this project.

### License

© 2015 Autodesk Inc.
All rights reserved

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
