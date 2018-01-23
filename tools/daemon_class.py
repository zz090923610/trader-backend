import os
import threading
import time
import paho.mqtt.client as mqtt
import paho.mqtt.publish as single_publish


class DaemonClass:
    def __init__(self, topic_sub=None, topic_pub='', auth=None, name=''):

        if topic_sub is None:
            topic_sub = []
        self.client = mqtt.Client()
        self.client.on_connect = self.mqtt_on_connect
        self.client.on_message = self.mqtt_on_message
        self.client.on_subscribe = self.mqtt_on_subscribe
        self.client.on_publish = self.mqtt_on_publish
        self.alive_name = name
        if auth is not None:
            self.client.username_pw_set(auth['username'], auth['password'])
        self.client.connect("localhost", 1883, 60)
        self.mqtt_topic_sub = topic_sub
        self.mqtt_topic_pub = topic_pub
        self.cancel_daemon = False
        self.msg_on_exit = ''

    def mqtt_on_connect(self, mqttc, obj, flags, rc):
        if type(self.mqtt_topic_sub) == list:
            for t in self.mqtt_topic_sub:
                mqttc.subscribe(t)
        elif type(self.mqtt_topic_sub) == str:
            mqttc.subscribe(self.mqtt_topic_sub)

    def mqtt_on_message(self, mqttc, obj, msg):
        payload = msg.payload.decode('utf8')
        if payload == 'exit':
            self.publish(self.msg_on_exit)
            self.cancel_daemon = True

    def publish(self, msg, qos=0):
        (result, mid) = self.client.publish(self.mqtt_topic_pub, msg, qos)

    def unblock_publish(self, msg, qos=0):
        single_publish.single(self.mqtt_topic_pub, payload=msg,
                              qos=qos, retain=False, hostname="localhost",
                              port=1883, client_id="", keepalive=60, will=None, auth=None,
                              tls=None, protocol=mqtt.MQTTv31)

    def mqtt_on_publish(self, mqttc, obj, mid):
        pass

    def mqtt_on_subscribe(self, mqttc, obj, mid, granted_qos):
        pass

    # noinspection PyMethodMayBeStatic
    def mqtt_on_log(self, mqttc, obj, level, string):
        pass

    def MQTT_CANCEL(self):
        self.client.loop_stop(force=True)
        pass

    def MQTT_START(self):
        threading.Thread(target=self.client.loop_start).start()
        pass

    def daemon_main(self):
        self.MQTT_START()
        self.publish('%s/alive_%d' % (self.alive_name, os.getpid()))
        while not self.cancel_daemon:
            time.sleep(.5)
        self.MQTT_CANCEL()
