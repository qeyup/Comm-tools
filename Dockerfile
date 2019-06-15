FROM ubuntu:18.04


RUN mkdir /docker
COPY . /docker/
ADD https://raw.githubusercontent.com/qeyup/DockerBuild/master/DockerBuild.sh /docker/
RUN  cd /docker && chmod u+x DockerBuild.sh && ./DockerBuild.sh


# Change work dir
WORKDIR /root


# Build command help: 
# sudo docker build -t "$(basename $PWD | sed -e s/DockerBuild_//g):$(git branch | grep \* | sed -e s/'\* '//g | sed -e s/'\/'/-/g)" .
