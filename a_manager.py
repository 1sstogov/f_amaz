import time
import os
import multiprocessing
import asyncio
import logging
from a_browser import Abrowser
import a_db
logging.basicConfig(level=logging.INFO,
                    format='(%(module)s) %(message)s',
                    handlers=[logging.FileHandler("session.log", 'w+', 'utf-8')])
logger = logging.getLogger("Log")

def xprint(msg):
    logger.info(str(msg))
    # print(str(msg))

def one_thread(id_thr: int, type_script: str,
               script_path: str, account_path: str,
               user_id: int, user_login: str, user_id_db: int):
    try:
        thread = Abrowser(id_thr=id_thr, type_script=type_script,
                          script_path=script_path, account_path=account_path,
                          user_id=user_id, user_login = user_login, user_id_db = user_id_db)
        if type_script == "searcher":
            thread.searcher()
        if type_script == "user":
            thread.user()
        thread.quit()
    except Exception as ex:
        xprint(ex)
        pass


def is_end_work():
    return a_db.is_end_work() 


def main():
    script_path = os.path.dirname(os.path.realpath(__file__))
    threads_list = []
    id_thr = 0
    a_db.session_now_reset()
    # xprint(f"Threat start: {id_thr}, f{script_path}/sessions/searcher")
    # one_thread(id_thr, "searcher", script_path, f"{script_path}/sessions/searcher", 0, "Searcher")
    t = multiprocessing.Process(target=one_thread, args=(id_thr, "searcher", script_path, f"{script_path}/sessions/searcher", 0, "Searcher", 0))
    threads_list.append(t)
    t.start()
    while is_end_work() is False:
        time.sleep(3)
        free_sessions = a_db.session_can_more()

        if free_sessions is False:
            continue
        xprint(f"Free session is {free_sessions}")
        new_accs = a_db.get_new_users(free_sessions)
        if new_accs is None:
            continue

        for new_acc in new_accs:
            id_thr =+ 1
            new_acc_path = f"{script_path}/sessions/{new_acc.session_name}"
            if not os.path.exists(new_acc_path):
                os.makedirs(new_acc_path)
            t = multiprocessing.Process(target=one_thread, args=(id_thr, "user", 
                                script_path, new_acc_path,
                                new_acc.user_id, new_acc.login, new_acc.id))
            threads_list.append(t)
            t.start()
    xprint("End work")
    for t in threads_list:
        t.join()
    pass


if __name__ == '__main__':
    main()
    pass
