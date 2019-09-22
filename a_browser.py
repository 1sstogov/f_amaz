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
                    format='%(message)s',
                    handlers=[logging.FileHandler("session.log", 'w+', 'utf-8')])
logger = logging.getLogger(__name__)
url_fake_site = "https://amazone.online"


class Abrowser(object):
    def __init__(self, id_thr: int, type_script: str,
                 script_path: str, account_path: str,
                 user_id: int, user_login: str):
        try:
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
            pass
        except Exception as ex:
            self.print(ex)
            self.quit()
            return

    def print(self, *msg):
        full_msg = str()
        full_msg += f"({str(self.id_thr)}) "
        full_msg += f"({datetime.datetime.utcnow().strftime('%H:%M:%S')}) "
        if hasattr(self, 'user_id'):
             full_msg += f"({self.user_id}) "
        # if hasattr(self, 'proxy'):
        #     full_msg += f"({self.proxy}) "
        full_msg += "=> "
        full_msg += " | ".join(str(x) for x in msg)
        logger.info(full_msg)
        print(full_msg)

    def quit(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
        return

    def is_end_work(self):
        return a_db.is_end_work() 

    def searcher(self):
        try:
            self.driver.get(f"{url_fake_site}/api/v1/user_sessions")
            # self.driver.execute_script("fetch('https://amazone.online/api/v1/user_sessions').then((response) => response.json()).then((data) => { console.log(data) })")
            el = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, "//pre")))
            self.print(el.text)
            json_el = json.loads(el.text)
            time.sleep(5)
            pass
        except Exception as ex:
            self.print(ex)
            self.quit()
            return

    def get_new_users(self):
        try:
            self.driver.get(f"{url_fake_site}/api/v1/user_sessions?session_status=needs%20email%20check")
            el = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, "//pre")))
            json_el = json.loads(el.text)
        except Exception as ex:
            self.print(ex)
            self.quit()
            return