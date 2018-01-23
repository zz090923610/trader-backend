import os
from time import sleep

import selenium.common.exceptions as SExceptions
from selenium import webdriver

from tools.date_util.market_calendar_cn import MktCalendar
from tools.io import logging

chromedriver = "chromedriver"
os.environ["webdriver.chrome.driver"] = chromedriver

import trader.account_info as account

status_dict = {'sleep': ['action_prelogin'],
               'wait_verify_code': ['action_login_with_verify_code','action_prelogin'],
               'active': ['action_buy', 'action_sell', 'action_cash', 'action_heart_beat','action_prelogin']}


class TradeAPI:
    # DEPENDENCY( selenium )
    def __init__(self, headless=False, auth=None):
        self.driver = None
        self.user = account.user
        self.passwd = account.passwd
        self.on_server = account.on_server
        self.options = webdriver.ChromeOptions()
        self.headless = headless
        self.busy = False
        self.auth=auth
        self.status = 'sleep'
        self.mkt_cal = MktCalendar()
        if headless:
            self.options.add_argument('headless')

    def respond(self, payload, res_type='str'):
        if self.on_server:
            from tools.communication.mqtt import simple_publish
            simple_publish("trade_res/%s" % res_type, payload, auth=self.auth)
        if res_type == "str":
            logging("logging", payload, method=account.logging_method)

    # noinspection PyBroadException
    def __del__(self):
        try:
            self.driver.close()
        except Exception:
            pass

    def get_current_allowed_actions(self):
        try:
            action_list = status_dict[self.status]
        except KeyError:
            action_list = []
        return action_list

    def pre_login(self):
        if 'action_prelogin' not in self.get_current_allowed_actions():
            self.respond("TradeAPI/StatusActionNotMatch:%s/%s" % (self.status, "action_prelogin"))
            return
        self.driver = webdriver.Chrome(chromedriver, chrome_options=self.options)
        self.driver.get('https://trade.gtja.com/webtrade/trade/webTradeAction.do?method=preLogin')
        e = self.driver.find_element_by_name("YYBFW")
        f = e.find_element_by_xpath("//input[@id='all_yybfw']")
        f.find_element_by_xpath("//input[@value='5']").click()  # hua bei
        g = self.driver.find_element_by_name("BranchCode")
        g.find_element_by_xpath("//option[@title='山西太原建设南路营业部']").click()
        self.driver.find_element_by_name("inputid").send_keys(self.user)
        self.driver.find_element_by_name("trdpwd").send_keys(self.passwd)
        self.driver.get_screenshot_as_file('/tmp/main-page.png')
        from PIL import Image
        image = Image.open('/tmp/main-page.png')
        area = (0, 0, 400, 600)
        image = image.crop(area)
        image.save('/tmp/main-page.png')
        if self.headless and not self.on_server:
            image.show()
        self.status = 'wait_verify_code'
        if self.headless and self.on_server:
            with open('/tmp/main-page.png', 'rb') as f:
                image = f.read()
                payload = bytearray(image)
                self.respond(payload, res_type='img')
                self.respond("TradeAPI/verify_image_sent")

    def resend_verify_image(self):
        try:
            with open('/tmp/main-page.png', 'rb') as f:
                image = f.read()
                payload = bytearray(image)
                self.respond(payload, res_type='img')
                self.respond("TradeAPI/verify_image_sent")
        except Exception as e:
            pass

    def login_with_verify_code(self, verify_code):
        if 'action_login_with_verify_code' not in self.get_current_allowed_actions():
            self.respond("TradeAPI/StatusActionNotMatch:%s/%s" % (self.status, "action_login_with_verify_code"))
            return
        self.driver.find_element_by_name("AppendCode").send_keys(verify_code)
        self.driver.find_element_by_id("confirmBtn").click()
        t = self.driver.find_element_by_id("show_msg_div")
        t.find_element_by_xpath("//img[@src='/webtrade/pic/images/chahao.png']").click()
        try:
            alert = self.driver.switch_to_alert()
            self.respond("TradeAPI/login_failed_%s" % alert.text)
            self.status = 'sleep'
        except SExceptions.NoAlertPresentException:
            if self.driver.title == '国泰君安证券欢迎您':
                self.respond("TradeAPI/login_success")
                self.status = 'active'
            else:
                self.respond("TradeAPI/login_failed")
                self.status = 'sleep'

    def send_heartbeat(self):
        if 'action_heart_beat' not in self.get_current_allowed_actions():
            self.respond("TradeAPI/StatusActionNotMatch:%s/%s" % (self.status, "action_heart_beat"))
            return
        if self.busy:
            return
        self.driver.get("https://trade.gtja.com/webtrade/trade/PaperBuy.jsp")
        try:
            alert = self.driver.switch_to_alert()
            self.respond("TradeAPI/heartbeat_%s_%s" % (alert.text, self.mkt_cal.get_local_time()))
            self.status = 'sleep'
        except SExceptions.NoAlertPresentException:
            self.respond("TradeAPI/heartbeat_success_%s" % self.mkt_cal.get_local_time())
            self.status = 'active'

    def buy(self, symbol, price, quant):
        if 'action_buy' not in self.get_current_allowed_actions():
            self.respond("TradeAPI/StatusActionNotMatch:%s/%s" % (self.status, "action_buy"))
            return
        while self.busy:
            sleep(1)
        self.busy = True
        self.driver.get("https://trade.gtja.com/webtrade/trade/PaperBuy.jsp")
        self.driver.find_element_by_name("stkcode").clear()
        self.driver.find_element_by_name("qty").clear()
        self.driver.find_element_by_name("price").clear()
        self.driver.find_element_by_name("stkcode").send_keys(symbol)
        self.driver.find_element_by_name("price").send_keys(price)
        self.driver.find_element_by_name("qty").send_keys(quant)
        sleep(0.3)
        self.driver.find_element_by_name("radiobutton").click()
        self.driver.find_element_by_name("Submit").click()
        handle = self.driver.current_window_handle
        try:
            alert = self.driver.switch_to_alert()
            alert.accept()
            self.driver.switch_to.window(handle)
        except SExceptions.NoAlertPresentException:
            self.respond("TradeAPI/NoAlertPresentException_BUY_POS1")
        try:
            alert = self.driver.switch_to_alert()
            self.respond("TradeAPI/buy_%s_%s_%s/%s" % (symbol, price, quant, alert.text))
            alert.dismiss()
        except SExceptions.NoAlertPresentException:
            self.respond("TradeAPI/NoAlertPresentException_BUY_POS2")
        self.busy = False

    def sell(self, symbol, price, quant):
        if 'action_sell' not in self.get_current_allowed_actions():
            self.respond("TradeAPI/StatusActionNotMatch:%s/%s" % (self.status, "action_sell"))
            return
        while self.busy:
            sleep(1)
        self.busy = True
        self.driver.get("https://trade.gtja.com/webtrade/trade/Papersale.jsp")
        self.driver.find_element_by_name("price").clear()
        self.driver.find_element_by_name("stkcode").clear()
        self.driver.find_element_by_name("qty").clear()

        self.driver.find_element_by_name("stkcode").send_keys(symbol)
        self.driver.find_element_by_name("price").send_keys(price)
        self.driver.find_element_by_name("qty").send_keys(quant)

        sleep(0.3)
        self.driver.find_element_by_name("radiobutton").click()
        self.driver.find_element_by_name("Submit2").click()
        handle = self.driver.current_window_handle
        try:
            alert = self.driver.switch_to_alert()
            alert.accept()
            self.driver.switch_to.window(handle)
        except SExceptions.NoAlertPresentException:
            self.respond("TradeAPI/NoAlertPresentException_SELL_POS1")
        try:
            alert = self.driver.switch_to_alert()
            self.respond("TradeAPI/sell_%s_%s_%s/%s" % (symbol, price, quant, alert.text))
            alert.dismiss()
        except SExceptions.NoAlertPresentException:
            self.respond("TradeAPI/NoAlertPresentException_SELL_POS2")
        self.busy = False

    def get_available_cash(self):
        if 'action_cash' not in self.get_current_allowed_actions():
            self.respond("TradeAPI/StatusActionNotMatch:%s/%s" % (self.status, "action_cash"))
            return
        self.driver.get("https://trade.gtja.com/webtrade/trade/webTradeAction.do?method=searchStackDetail")
        cash = self.driver.find_element_by_xpath(
            "/html/body/table/tbody/tr/td/table[1]/tbody/tr/td[1]/table[2]/tbody/tr/td/table/tbody/tr[2]/td[4]").text
        self.respond("TradeAPI/cash_%s" % cash)
        return float(cash)
