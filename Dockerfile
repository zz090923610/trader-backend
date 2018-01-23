FROM ubuntu-chrome-driver

WORKDIR /
RUN apt-get -qq -y update && \
	apt-get -qq -y install mosquitto \
	mosquitto-clients \
	 && rm -rf /var/lib/apt/lists/*

EXPOSE 1883
ADD ./etc/mosquitto/* /etc/mosquitto/


RUN apt-get -qq update && \ 
	apt-get install -qq -y python3-pip
RUN pip3 install selenium \
				 paho-mqtt \
				 pytz \
				 requests \
				 beautifulsoup4 \
				 lxml \
				 pandas \
				 pillow
RUN pip3 install tushare

RUN mkdir /root/trader-backend
ADD . /root/trader-backend
RUN rm -rf /root/trader-backend/etc
RUN rm  /root/trader-backend/Dockerfile
RUN ln -s /root/trader-backend/backend.run /bin/
