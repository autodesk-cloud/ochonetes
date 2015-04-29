FROM paugamo/pod

#
# - install jdk8 from oracle
#
RUN apt-get install -y python-software-properties software-properties-common
RUN add-apt-repository ppa:webupd8team/java
RUN apt-get update
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
RUN apt-get update && apt-get install -y oracle-java8-installer

#
# - setup zk 3.4.6 straight from their mirror
#
RUN wget -q -O - http://apache.mirrors.pair.com/zookeeper/zookeeper-3.4.6/zookeeper-3.4.6.tar.gz | tar -C /opt -xz
RUN mkdir /var/lib/zookeeper

#
# - add our spiffy pod script
# - add the zookeeper supervisor config file
# - start supervisor
#
ADD resources/pod /opt/zookeeper-3.4.6/pod
ADD resources/supervisor /etc/supervisor/conf.d
CMD /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
