FROM ubuntu-chrome-driver

RUN mkdir /root/trader-backend
ADD . /root/trader-backend
RUN rm -rf /root/trader-backend/etc
RUN rm  /root/trader-backend/Dockerfile
RUN ln -s /root/trader-backend/backend.run /bin/
