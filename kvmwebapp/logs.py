from datetime import datetime


def action_log(somebody, action_description):
    with open(f"kvmwebapp/logs/{datetime.now().strftime('%d-%m-%Y')}.txt", "a") as f:
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(f"{now} | {somebody} - {action_description}")
