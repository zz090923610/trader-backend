import os
import time

import pandas as pd
import pytz
from tushare import trade_cal
from tushare.util.dateu import last_tddate




class MktCalendar:
    # DEPENDENCY( tushare pytz )
    # TODO: generate calendar if not exist
    def __init__(self, tz='Asia/Shanghai', mkt='CN'):
        self.timezone = tz
        self.market = mkt
        try:
            from configs.path import DIRs
            self.cal_path = os.path.join(DIRs.get("CALENDAR"), "%s.csv" % self.market)
        except Exception as e:
            self.cal_path = "%s.csv" % self.market
        self.cal = self.load_calendar()
        self.quick_dict = self.build_quick_dict()

    def load_calendar(self):
        try:
            return pd.read_csv(self.cal_path)
        except FileNotFoundError:
            a = trade_cal()
            a.to_csv(self.cal_path, index=False)
            return a
        except Exception as e:
            return None

    def build_quick_dict(self):
        list_of_dict = self.cal.to_dict('records')
        quick_dict = {}
        for l in list_of_dict:
            quick_dict[l['calendarDate']] = l['isOpen']
        return quick_dict

    def update_calendar(self):
        self.cal = trade_cal()
        self.cal.to_csv(self.cal_path, index=False)

    def _get_local_now(self):
        from datetime import datetime
        current_time = time.time()
        utc_now, now = datetime.utcfromtimestamp(current_time), datetime.fromtimestamp(current_time)
        return utc_now.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(self.timezone))

    def get_local_date(self):
        """
        return today's date in YYYY-MM-DD format
        :param tz: time zone
        :return: string
        """
        local_now = self._get_local_now()
        local_today = local_now.strftime("%Y-%m-%d")
        return local_today

    def get_local_time(self):
        local_now = self._get_local_now()
        local_time = local_now.strftime("%H:%M:%S")
        return local_time

    def gen_date_list(self, goal, t='TODAY', in_mkt=False):
        # TODO
        if goal == "T" and t == 'TODAY':
            return [self.get_local_date()] if not in_mkt else [last_tddate()]

    def validate_date(self, day):
        if day == "TODAY":
            local_date_now = self.get_local_date()
            return local_date_now if self.quick_dict[local_date_now] == 1 else last_tddate()
        if day == "LASTCLOSEDTRADEDAY":
            local_date_now = self.get_local_date()
            local_time_now = self.get_local_time()
            return local_date_now if self.quick_dict[local_date_now] == 1 and local_time_now >= '15:05:00' \
                else last_tddate()
        else:
            return day  # FIXME

    def get_day(self, target, t='TODAY'):
        # TODAY+1
        # 2018-01-01+5
        t = self.validate_date(t)
        req_ascending = True if '+' in target else False
        day_diff = target.split("+")[1] if req_ascending else target.split("-")[1]
        day_diff = int(day_diff)
        if req_ascending:
            sub_df = self.cal[self.cal['calendarDate'] >= t]
            sub_df = sub_df[sub_df['isOpen'] == 1]
        else:
            sub_df = self.cal[self.cal['calendarDate'] <= t].sort_values(by="calendarDate", ascending=False)
            sub_df = sub_df[sub_df['isOpen'] == 1]
        return sub_df.iloc[day_diff]['calendarDate']


