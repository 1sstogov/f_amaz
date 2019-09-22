import time
import os
import multiprocessing
import asyncio
from a_browser import Abrowser
import a_db


def one_thread(id_thr: int, type_script: str,
               script_path: str, account_path: str,
               user_id: int, user_login: str):
    try:
        thread = Abrowser(id_thr=id_thr, type_script=type_script,
                          script_path=script_path, account_path=account_path,
                          user_id=user_id, user_login = user_login)
        if type_script == "searcher":
            thread.searcher()
        if type_script == "user":
            print("I am User!")
        thread.quit()
    except Exception as ex:
        print(ex)
        pass


def is_end_work(script_path):
    with open(f"{script_path}/work.txt", 'r+') as file:
        file_work = int(file.readline())
        if file_work != 1:
            return True
        else:
            return False


def main():
    script_path = os.path.dirname(os.path.realpath(__file__))
    threads_list = []
    id_thr = 0
    print(f"Threat start: {id_thr}, f{script_path}/sessions/searcher")
    one_thread(id_thr, "searcher", script_path, f"{script_path}/sessions/searcher", 0, "Searcher")
    # t = multiprocessing.Process(target=one_thread, args=(id_thr, "searcher", 
    #                             script_path, f"{script_path}/sessions/searcher",
    #                             0))
    # threads_list.append(t)
    # t.start()
    # while is_end_work(script_path) is False:
    #     time.sleep(3)
    #     new_users = a_db.get_new_users()
    #     if new_users is not None:
    #         print(f"Found {len(new_users)} new users")
    #         for new_user in new_users:
    #             id_thr =+ 1
    #             new_user_path = f"{script_path}/sessions/{new_user.session_name}"
    #             if not os.path.exists(new_user_path):
    #                 os.makedirs(new_user_path)
    #             print(f"Threat start: {id_thr}, {new_user_path}")
    #             t = multiprocessing.Process(target=one_thread, args=(id_thr, "user", 
    #                             script_path, new_user_path,
    #                             new_user.user_id))
    #             threads_list.append(t)
    #             t.start()
    #     else:
    #         print(f"Not found new users")
    #     pass
    # print("End work")
    # for t in threads_list:
    #     t.join()
    pass


if __name__ == '__main__':
    main()
    pass
