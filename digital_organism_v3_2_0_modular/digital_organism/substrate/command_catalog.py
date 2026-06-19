from typing import Any, Dict, List
from digital_organism.substrate.command_specs import CommandSpec

def command_catalog_for(os_profile: Dict[str, Any]) -> List[CommandSpec]:
    return {
        "windows": windows_commands,
        "linux": linux_commands,
        "macos": macos_commands,
        "bsd": bsd_commands,
    }.get(os_profile["os_family"], generic_unix_commands)()

def windows_commands():
    return [
        CommandSpec("windows_version", ["cmd","/c","ver"], "os","observe","Windows version"),
        CommandSpec("systeminfo", ["systeminfo"], "os","observe","System summary", timeout=12, max_chars=30000),
        CommandSpec("ipconfig_all", ["ipconfig","/all"], "network","observe","Full IP configuration"),
        CommandSpec("route_print", ["route","print"], "network","observe","Routing table"),
        CommandSpec("arp_a", ["arp","-a"], "network","observe","ARP cache"),
        CommandSpec("netstat_ano", ["netstat","-ano"], "network","observe","Connections and listening ports", timeout=12, max_chars=30000),
        CommandSpec("netsh_interface_show_interface", ["netsh","interface","show","interface"], "network","observe","Interface status"),
        CommandSpec("tasklist", ["tasklist"], "processes","observe","Running process list", timeout=12, max_chars=30000),
        CommandSpec("services", ["sc","query","state=","all"], "services","observe","Service state", timeout=12, max_chars=30000),
        CommandSpec("schtasks_query", ["schtasks","/query","/fo","LIST"], "scheduled_tasks","observe","Scheduled task inventory", timeout=15, max_chars=30000),
        CommandSpec("winget_version", ["winget","--version"], "package_managers","observe","Detect winget", timeout=5),
        CommandSpec("choco_version", ["choco","--version"], "package_managers","observe","Detect Chocolatey", timeout=5),
        CommandSpec("scoop_version", ["scoop","--version"], "package_managers","observe","Detect Scoop", timeout=5),
        CommandSpec("tracert_target", ["tracert","{target}"], "network_path","trace","Trace route to explicit target", timeout=20, requires_explicit_target=True),
    ]

def linux_commands():
    return [
        CommandSpec("uname", ["uname","-a"], "os","observe","Kernel and architecture"),
        CommandSpec("os_release", ["cat","/etc/os-release"], "os","observe","Linux distribution release"),
        CommandSpec("uptime", ["uptime"], "os","observe","Uptime and load"),
        CommandSpec("ip_addr", ["ip","addr","show"], "network","observe","IP addresses"),
        CommandSpec("ip_route", ["ip","route","show"], "network","observe","IPv4 routes"),
        CommandSpec("ip_route6", ["ip","-6","route","show"], "network","observe","IPv6 routes"),
        CommandSpec("ip_neigh", ["ip","neigh","show"], "network","observe","Neighbor/ARP table"),
        CommandSpec("ss_tulpen", ["ss","-tulpen"], "network","observe","Sockets and listening ports", timeout=10, max_chars=30000),
        CommandSpec("ifconfig_a", ["ifconfig","-a"], "network","observe","Legacy interface view", timeout=8),
        CommandSpec("iptables_list", ["iptables","-L","-n","-v"], "firewall","observe","iptables rules read-only", timeout=10, max_chars=30000),
        CommandSpec("nft_list_ruleset", ["nft","list","ruleset"], "firewall","observe","nftables rules read-only", timeout=10, max_chars=30000),
        CommandSpec("ufw_status", ["ufw","status","verbose"], "firewall","observe","UFW read-only", timeout=8),
        CommandSpec("ps_aux", ["ps","aux"], "processes","observe","Process list", timeout=10, max_chars=30000),
        CommandSpec("systemctl_running", ["systemctl","list-units","--type=service","--state=running","--no-pager"], "services","observe","Running services", timeout=10, max_chars=30000),
        CommandSpec("mounts", ["mount"], "storage","observe","Mounted filesystems", timeout=8, max_chars=30000),
        CommandSpec("df_h", ["df","-h"], "storage","observe","Disk usage"),
        CommandSpec("lsblk", ["lsblk","-f"], "storage","observe","Block devices"),
        CommandSpec("apt_version", ["apt","--version"], "package_managers","observe","Detect apt", timeout=5),
        CommandSpec("dnf_version", ["dnf","--version"], "package_managers","observe","Detect dnf", timeout=5),
        CommandSpec("yum_version", ["yum","--version"], "package_managers","observe","Detect yum", timeout=5),
        CommandSpec("pacman_version", ["pacman","--version"], "package_managers","observe","Detect pacman", timeout=5),
        CommandSpec("zypper_version", ["zypper","--version"], "package_managers","observe","Detect zypper", timeout=5),
        CommandSpec("apk_version", ["apk","--version"], "package_managers","observe","Detect apk", timeout=5),
        CommandSpec("snap_version", ["snap","--version"], "package_managers","observe","Detect snap", timeout=5),
        CommandSpec("flatpak_version", ["flatpak","--version"], "package_managers","observe","Detect flatpak", timeout=5),
        CommandSpec("traceroute_target", ["traceroute","{target}"], "network_path","trace","Trace route", timeout=20, requires_explicit_target=True),
        CommandSpec("tracepath_target", ["tracepath","{target}"], "network_path","trace","Trace path", timeout=20, requires_explicit_target=True),
    ]

def macos_commands():
    return [
        CommandSpec("uname", ["uname","-a"], "os","observe","Kernel and architecture"),
        CommandSpec("sw_vers", ["sw_vers"], "os","observe","macOS version"),
        CommandSpec("ifconfig", ["ifconfig"], "network","observe","Interface configuration"),
        CommandSpec("route_default", ["route","-n","get","default"], "network","observe","Default route"),
        CommandSpec("netstat_rn", ["netstat","-rn"], "network","observe","Routing table"),
        CommandSpec("netstat_anv", ["netstat","-anv"], "network","observe","Connections", timeout=10, max_chars=30000),
        CommandSpec("arp_a", ["arp","-a"], "network","observe","ARP cache"),
        CommandSpec("scutil_dns", ["scutil","--dns"], "network","observe","DNS config", timeout=8),
        CommandSpec("ps_aux", ["ps","aux"], "processes","observe","Processes", timeout=10, max_chars=30000),
        CommandSpec("launchctl_services", ["launchctl","list"], "services","observe","launchd services", timeout=10, max_chars=30000),
        CommandSpec("df_h", ["df","-h"], "storage","observe","Disk usage"),
        CommandSpec("diskutil_list", ["diskutil","list"], "storage","observe","Disk layout", timeout=10, max_chars=30000),
        CommandSpec("brew_version", ["brew","--version"], "package_managers","observe","Detect Homebrew", timeout=5),
        CommandSpec("port_version", ["port","version"], "package_managers","observe","Detect MacPorts", timeout=5),
        CommandSpec("traceroute_target", ["traceroute","{target}"], "network_path","trace","Trace route", timeout=20, requires_explicit_target=True),
    ]

def bsd_commands():
    return [
        CommandSpec("uname", ["uname","-a"], "os","observe","Kernel and architecture"),
        CommandSpec("ifconfig", ["ifconfig"], "network","observe","Interface configuration"),
        CommandSpec("netstat_rn", ["netstat","-rn"], "network","observe","Routing table"),
        CommandSpec("netstat_an", ["netstat","-an"], "network","observe","Connections"),
        CommandSpec("arp_a", ["arp","-a"], "network","observe","ARP table"),
        CommandSpec("sockstat", ["sockstat","-4","-6"], "network","observe","Socket table", timeout=10, max_chars=30000),
        CommandSpec("pfctl_rules", ["pfctl","-sr"], "firewall","observe","pf rules read-only", timeout=8),
        CommandSpec("ps_aux", ["ps","aux"], "processes","observe","Processes", timeout=10, max_chars=30000),
        CommandSpec("service_list", ["service","-e"], "services","observe","Enabled services", timeout=8),
        CommandSpec("df_h", ["df","-h"], "storage","observe","Disk usage"),
        CommandSpec("pkg_info", ["pkg","info"], "package_managers","observe","pkg inventory", timeout=10, max_chars=30000),
        CommandSpec("traceroute_target", ["traceroute","{target}"], "network_path","trace","Trace route", timeout=20, requires_explicit_target=True),
    ]

def generic_unix_commands():
    return [
        CommandSpec("uname", ["uname","-a"], "os","observe","Kernel and architecture"),
        CommandSpec("ifconfig", ["ifconfig","-a"], "network","observe","Interface config"),
        CommandSpec("netstat_rn", ["netstat","-rn"], "network","observe","Routing table"),
        CommandSpec("ps_aux", ["ps","aux"], "processes","observe","Processes"),
        CommandSpec("df_h", ["df","-h"], "storage","observe","Disk usage"),
        CommandSpec("mount", ["mount"], "storage","observe","Mounts"),
    ]
