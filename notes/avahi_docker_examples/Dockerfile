FROM ubuntu:20.04
RUN apt update
RUN apt upgrade
RUN apt install avahi-utils -y
RUN apt install iputils-ping -y
COPY start.sh /usr/local/bin
COPY custom_tcp_service.service /etc/avahi/services
COPY custom_db_tcp_service.service /etc/avahi/services
RUN chmod +x /usr/local/bin/start.sh
ENTRYPOINT ["/bin/bash", "/usr/local/bin/start.sh"]
