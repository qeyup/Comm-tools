FROM ubuntu:18.04


RUN mkdir /docker
COPY . /docker/
ADD https://raw.githubusercontent.com/qeyup/DockerInstallTool/master/DockerInstall.sh /docker/
RUN  cd /docker && chmod u+x DockerInstall.sh && ./DockerInstall.sh


# Change work dir
WORKDIR /root