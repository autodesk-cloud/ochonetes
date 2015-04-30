Tools
=====

The tool set
____________

Overview
********

The *portal* application we run as a proxy embeds a whole bunch of tools. Those are all little standalone Python_
scripts that the *portal* will *POpen()* from a temporary directory. They all support a *--help* switch which displays
detailed information, supported parameters and so on.

You can also use the **help** command to print out a complete list of tools.

Container definitions
*********************

In order to deploy our Ochopod_ clusters we need to feed enough information to Kubernetes_ and deploy specific
constructs (*replication controllers* in the present case). This is all done by the **deploy** tool in a fairly
generic fashion.

Now we of course need to pass just enough data to quantify what we need to run, what ports to expose and so on. This
is done via a tiny YAML_ file I call a *container definition*. For instance:

.. code:: yaml

    cluster:  zookeeper
    image:    paugamo/k8s-ec2-zookeeper
    settings:
    ports:
        - 2181
        - 2888
        - 3888

This little snippet can be uploaded and passed to the **deploy** tool which will then turn it into a full-fledged
*replication controller* call to the K8S service API. Any required setting for Ochopod_ will be added in there as well
transparently.

Please note the *settings* block which can hold arbitrary nested data. This will be turned into a single serialized
JSON snippet and passed to the container as the *pod* environment variable. Very handy to specify complex runtime
settings.

.. note::

    Please note I decided to split image building & deployment as it turned out to be impractical to have the *portal*
    to build/push images on its own. With the current model you are assumed to have images already built somewhere,
    which is still fine.

Your clusters
*************

Once a Ochopod_ cluster is deployed you will get a new *replication controller* (plus a certain number of *pods*). Its
name will be assembled from the Ochopod_ cluster & namespace plus a unique timestamp. You don't have to worry about
how this is done, what the K8S API looks like and so on.

You can inspect your clusters at runtime using for instance the **grep**, **info** or **log** commands.


.. _Flask: http://flask.pocoo.org/
.. _JQuery: https://jquery.com/
.. _Kubernetes: https://github.com/GoogleCloudPlatform/kubernetes
.. _Ochopod: https://github.com/autodesk-cloud/ochopod
.. _Python: https://www.python.org/
.. _YAML: http://yaml.org/
