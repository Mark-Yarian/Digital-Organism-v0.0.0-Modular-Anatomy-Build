from typing import List
BLOCKED_WORDS = [" add "," delete "," remove "," rm "," rmdir "," format "," mkfs "," umount "," enable "," disable "," start "," stop "," restart "," kill "," taskkill "," shutdown "," reboot "," set "," new-"," set-"," remove-"," disable-"," enable-"]
ALLOWED_EXCEPTIONS = [" sc query state= all ", " systemctl list-units ", " systemctl list-timers ", " firewall-cmd --state ", " netsh interface show interface ", " netsh wlan show interfaces "]
def command_is_allowed(command: List[str]) -> bool:
    joined = " " + " ".join(command).lower() + " "
    if any(b in joined for b in BLOCKED_WORDS):
        return any(e in joined for e in ALLOWED_EXCEPTIONS)
    return True
