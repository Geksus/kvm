from datetime import datetime
import os


def action_log(somebody, action_description):
    directory_path = "kvmwebapp/logs"
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    with open("kvmwebapp/logs/the_one_and_only_log.txt", "a") as f:
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(f"{now} | {somebody} - {action_description}")
