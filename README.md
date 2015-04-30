## Ochonetes

### Overview

This project is a small development PaaS leveraging [**Ochopod**](https://github.com/autodesk-cloud/ochopod)
and overlaying it on top of [**Kubernetes**](https://github.com/GoogleCloudPlatform/kubernetes).

It provides a self-contained web-shell ([**JQuery**](https://jquery.com/) rocks !) hosting our little toolkit that will
allow you to create, query and manage your ochopod containers. It also lets you CURL your commands directly which is
a great way to build your CI/CD pipeline !

Please note we only support bindings to run over AWS at this point.

### Getting started

#### Step 1 : install K8S on AWS

You know how to do it. Just peruse their [**AWS guide**](https://github.com/GoogleCloudPlatform/kubernetes/blob/master/docs/getting-started-guides/aws.md)
that will get you setup in minutes.

Note what the master IP is and what your credentials. These can be found locally, for instance:

```
$ cat ~/.kube/kubernetes/kubernetes_auth
```

#### Step 2 : deploy our proxy

We use a simple proxy mechanism to interact with our containers. Edit the provided ```ocho-proxy.yml``` and specify
the master IP and user credentials. Then create the pod:

```
$ kubectl create -f ocho-proxy.yml
```

Wait a bit until the pod is up and note the public IP it is running on. This IP will be the only thing you need to
access from now on. You can easily firewall it depending on your needs. Simply use your browser and look the proxy
node IP up on port 9000. You should see our little web-shell (notice to elegant ascii art).

### Deploying your first container

Go ahead and use your new proxy to deploy a 3 node [**Zookeeper**](https://zookeeper.apache.org/) ensemble ! Look
at the little ```zookeeper.yml```. This is the container definition you are going to send to the proxy for deployment.
The proxy will then setup the corresponding k8s infrastructure (replication controller & pods) for you and ochopod will
automatically cluster those pods into a functional cross-configured ensemble.

The deployment is done from your machine via a simple CURL:

```
$ curl -X POST -H "X-Shell:deploy zk -p 3" -F "zk=@zookeeper.yml" http://<PROXY NODE IP>:9000/shell
```

Peek into the web-console and look your new ocho cluster up. For instance:

```
> grep
<*> -> 100% replies (4 pods total) ->
cluster                |  pod IP        |  process  |  state
                       |                |           |
default.ocho-proxy #0  |  10.244.1.35   |  running  |  leader
default.zookeeper #0   |  10.244.1.40   |  stopped  |  leader (configuration pending)
default.zookeeper #1   |  10.244.1.39   |  stopped  |  follower
default.zookeeper #2   |  10.244.2.105  |  stopped  |  follower
```

Wait a bit for the cluster to settle and poof you will have a nice ensemble you can access at TCP 2181 !

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