# Version 0.2.1
# Author Zhao Zhang<zz156@georgetown.edu>
# stock/common/communication.py
# 通信模块: 用于程序中不同组件间通信, 使用MQTT协议, 以应付未来组件分布式部署的潜在需求.
# 信息接收方须保持长连接, 实例化 MQTTHdl, 并 subscribe 相关主题.
# 连接操作在实例初始化时自动进行, 之后须手动进行 mqtt_sub_thread_start 启动新线程 subscribe. 完成时需要 mqtt_sub_thread_cancel 停止
# 监听线程.
# 获得消息的处理方法通过重载 mqtt_on_message 实现.
# 信息发送方较为宽松, 如已有 MQTTHdl 实例, 可使用实例之 publish 方法进行数据发送, 可省略连接操作开销. 若无可访问实例, 可调用
# simple_publish 方法进行数据传送.

# DEPENDENCY( paho-mqtt )
import threading

import paho.mqtt.client as mqtt
import paho.mqtt.publish as s_publish


DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 1883


def simple_publish(topic, payload, auth=None):
    s_publish.single(topic, payload=payload, qos=0, retain=False, hostname=DEFAULT_HOST,
                     port=DEFAULT_PORT, client_id="", keepalive=60, will=None, auth=auth,
                     tls=None, protocol=mqtt.MQTTv31)


class MQTTHdl:
    def __init__(self, topic_sub=None, topic_pub='', client_title='Default', hostname='localhost', port=1883):
        if topic_sub is None:
            topic_sub = []
        self.client = mqtt.Client()
        self.host = hostname
        self.port = port
        self.client.on_connect = self.mqtt_on_connect
        self.client.on_message = self.mqtt_on_message
        self.client.on_subscribe = self.mqtt_on_subscribe
        self.client.on_publish = self.mqtt_on_publish
        self.mqtt_topic_sub = topic_sub
        self.mqtt_topic_pub = topic_pub
        self.client_title = client_title
        self.cancel_daemon = False
        self.msg_on_exit = ''
        self.client.connect(self.host, self.port, 60)

    def mqtt_on_connect(self, mqttc, obj, flags, rc):
        if type(self.mqtt_topic_sub) == list:
            for t in self.mqtt_topic_sub:
                mqttc.subscribe(t)
        elif type(self.mqtt_topic_sub) == str:
            mqttc.subscribe(self.mqtt_topic_sub)

    def mqtt_on_message(self, mqttc, obj, msg):
        payload = msg.payload.decode('utf8')
        print(payload)
        if payload == 'exit':
            self.publish(self.msg_on_exit)
            self.cancel_daemon = True

    def publish(self, msg, qos=0, topic=''):
        if topic == '':
            topic = self.mqtt_topic_pub
        (result, mid) = self.client.publish(topic, msg, qos)

    def unblock_publish(self, msg, qos=0):
        s_publish.single(self.mqtt_topic_pub, payload=msg,
                         qos=qos, retain=False, hostname=self.host,
                         port=self.port, client_id="", keepalive=60, will=None, auth=None,
                         tls=None, protocol=mqtt.MQTTv31)

    def mqtt_on_publish(self, mqttc, obj, mid):
        pass

    def mqtt_on_subscribe(self, mqttc, obj, mid, granted_qos):
        pass

    # noinspection PyMethodMayBeStatic
    def mqtt_on_log(self, mqttc, obj, level, string):
        pass

    def mqtt_sub_thread_cancel(self):
        self.client.loop_stop(force=True)

    def mqtt_sub_thread_start(self):
        threading.Thread(target=self.client.loop_start).start()

    def mqtt_disconnect(self):
        self.client.disconnect()

    def mqtt_reconnect(self):
        self.client.connect(self.host, self.port, 60)
