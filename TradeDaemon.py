#!/usr/bin/env python
# -*- coding:utf-8 -*-
import threading
import time

from tools.daemon_class import DaemonClass
from trader.account_info import AUTH
from trader.api_driver import TradeAPI
from tools.io import logging

class TradeDaemon(DaemonClass):
    def __init__(self, topic_sub='trade_req', topic_pub='trade_res/str', auth=None, name="TradeDaemon"):
        super().__init__(topic_sub=topic_sub, topic_pub=topic_pub, auth=auth, name=name)
        self.trade_api = TradeAPI(headless=True, auth=AUTH)
        self.captcha_db = {}
        self.heart_thread = None
        self.keep_heartbeat = False
        #threading.Thread(target=self.status_report, daemon=True).start()

    def heart_beat(self):
        self.keep_heartbeat = True
        self.trade_api.respond('TradeDaemon/heartbeat_started')
        cnt = 0
        while self.keep_heartbeat:
            time.sleep(.5)
            cnt += 1
            if cnt == 240:
                self.trade_api.send_heartbeat()
                cnt = 0
            if self.trade_api.status != 'active':
                self.keep_heartbeat = False
                return

    #def status_report(self):
    #    while not self.cancel_daemon:
    #        self.trade_api.respond('TradeDaemon/status_%s' % self.trade_api.status)
    #        time.sleep(1)

    def mqtt_on_message(self, mqttc, obj, msg):
        payload = msg.payload.decode('utf8')
        logging("INCOMING REQ", payload)
        if payload == 'prelogin':
            self.keep_heartbeat = False
            self.trade_api.pre_login()
        elif payload == 'cash':
            self.trade_api.get_available_cash()
        elif payload == 'status':
            self.trade_api.respond('TradeDaemon/status_%s' % self.trade_api.status)
        elif payload == 'exit':
            self.cancel_daemon = True
            self.keep_heartbeat = False
        elif payload == 'resend_verify_image':
            self.trade_api.resend_verify_image()
        elif payload == 'sleep':
            self.keep_heartbeat = False
            self.trade_api.status = 'sleep'
        elif payload.split("_")[0] == "login":
            self.trade_api.login_with_verify_code(payload.split("_")[1])
            if self.trade_api.status == 'active':
                self.heart_thread = threading.Thread(target=self.heart_beat, daemon=True)
                self.heart_thread.start()
        elif payload.split("_")[0] == "buy":
            (b, symbol, price, quant) = payload.split("_")
            threading.Thread(target=self.trade_api.buy, args=(symbol, price, quant)).start()
        elif payload.split("_")[0] == "sell":
            (s, symbol, price, quant) = payload.split("_")
            threading.Thread(target=self.trade_api.sell, args=(symbol, price, quant)).start()


if __name__ == '__main__':
    a = TradeDaemon(auth=AUTH)
    a.daemon_main()
