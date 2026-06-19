import os, platform, socket
from pathlib import Path
from typing import Any, Dict
from digital_organism.core.utils import hash_value, safe_path_value

def detect_linux_distro() -> Dict[str, Any]:
    data={}; p=Path("/etc/os-release")
    if p.exists():
        for line in p.read_text(errors="ignore").splitlines():
            if "=" in line:
                k,v=line.split("=",1); data[k]=v.strip().strip('"')
    return {"id": data.get("ID"), "name": data.get("NAME"), "version": data.get("VERSION"), "version_id": data.get("VERSION_ID"), "id_like": data.get("ID_LIKE")}

def detect_os_profile() -> Dict[str, Any]:
    system=platform.system().lower()
    profile={"system": system, "release": platform.release(), "version": platform.version(), "machine": platform.machine(), "platform": platform.platform(), "hostname_hash": hash_value(socket.gethostname()), "python_version": platform.python_version(), "os_family": "unknown", "distro": None, "layout": {}}
    if system=="windows": profile.update(os_family="windows", layout=windows_layout())
    elif system=="linux": profile.update(os_family="linux", distro=detect_linux_distro(), layout=linux_layout())
    elif system=="darwin": profile.update(os_family="macos", layout=macos_layout())
    elif "bsd" in system: profile.update(os_family="bsd", layout=bsd_layout())
    else: profile.update(os_family="unix_like", layout=generic_unix_layout())
    return profile

def windows_layout():
    return {"system_root": os.environ.get("SystemRoot","C:\\Windows"), "program_files": os.environ.get("ProgramFiles","C:\\Program Files"), "program_data": os.environ.get("ProgramData","C:\\ProgramData"), "users_root":"C:\\Users", "user_profile": safe_path_value(os.environ.get("USERPROFILE","")), "temp": safe_path_value(os.environ.get("TEMP","")), "path_separator":"\\"}
def linux_layout():
    return {"root":"/","etc":"/etc","bin":"/bin","sbin":"/sbin","usr":"/usr","var":"/var","var_log":"/var/log","home":"/home","tmp":"/tmp","opt":"/opt","proc":"/proc","sys":"/sys","dev":"/dev","run":"/run","mnt":"/mnt","media":"/media","path_separator":"/"}
def macos_layout():
    return {"root":"/","applications":"/Applications","system":"/System","library":"/Library","users":"/Users","volumes":"/Volumes","private_etc":"/private/etc","private_var":"/private/var","usr_local":"/usr/local","opt_homebrew":"/opt/homebrew","path_separator":"/"}
def bsd_layout():
    return {"root":"/","etc":"/etc","bin":"/bin","sbin":"/sbin","usr":"/usr","usr_local":"/usr/local","var":"/var","home":"/home","tmp":"/tmp","ports":"/usr/ports","path_separator":"/"}
def generic_unix_layout():
    return {"root":"/","etc":"/etc","usr":"/usr","var":"/var","home": safe_path_value(str(Path.home())), "tmp":"/tmp","path_separator":"/"}
