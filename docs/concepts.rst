Concepts
========

Architecture
____________

Overview
********

Ochonetes is simply a Kubernetes_ pod that runs both a standalone Zookeeper_ plus a little *portal* Python_ application
(which interestingly is an Ochopod_ container itself). The *portal* job is to host a set of tools that will talk to
the Kubernetes_ master and Ochopod_ containers (for instance to deploy stuff).

Why using such a proxy mechanism ? Well, mostly to encapsulate logic and avoid ending up with a fat CLI on your end.
Additionally this allows to have all the inter-container I/O performed within the cluster (e.g no firewalling headache
for you). Of course for a real PaaS this is also where you would inject access control, credentials and so on.

In other words you deploy our *proxy* pod and talk to it from then on. Easy.

Why Ochopod ?
*************

Because Kubernetes_ - even if totally awesome - will not perform fine grained orchestration for you. You know what I
mean by fine grained: the ability to form relationships between your containers without the need for an extrinsic
control mechanism (look at the Ochopod_ documentation for more details).

In our case we will leverage the *replication controller* semantics from Kubernetes_. One Ochopod_ cluster maps to one
or more replication controllers. Each controller runs a bunch of pods which in turn run a Docker_ container embedding
Ochopod_.

Thanks to the super cool Kubernetes_ design we don't even bother about port remapping. The pod IP is all we need.

Where is Zookeeper ?
********************

As you remember Ochopod_ relies on Zookeeper_ for its internal leader elections and metadata storage. Our containers
will simply look the *proxy* pod up and use that IP (the said *proxy* colocates the *portal* and a Zookeeper_ process).

.. note::
    Yes I know you are going to say I just use a single standalone Zookeeper_ which is not really HA. This is true
    at the moment but we will probably morph the design a bit soon to lift this constraint. We potentially could
    leverage the cluster's Etcd_ instead.

.. _Docker: https://www.docker.com/
.. _Etcd: https://github.com/coreos/etcd
.. _Flask: http://flask.pocoo.org/
.. _Kubernetes: https://github.com/GoogleCloudPlatform/kubernetes
.. _Ochopod: https://github.com/autodesk-cloud/ochopod
.. _Python: https://www.python.org/
.. _Zookeeper: http://zookeeper.apache.org/

