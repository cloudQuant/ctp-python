#!/usr/bin/env python
"""Check Hongyuan CTP front addresses reachability."""
import socket

# 宏源期货环境
HONGYUAN_FRONTS = {
    "telecom": {
        "td": "101.230.79.235:32205",
        "md": "101.230.79.235:32213",
    },
    "unicom": {
        "td": "112.65.19.116:32205",
        "md": "112.65.19.116:32213",
    },
}

def check_tcp(host, port, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, int(port)))
        s.close()
        return True
    except Exception:
        return False

print("=" * 60)
print("Hongyuan CTP Front Reachability Check")
print("=" * 60)

reachable_env = None
for env_name, fronts in HONGYUAN_FRONTS.items():
    print(f"\n{env_name.upper()}:")
    td_host, td_port = fronts['td'].split(':')
    md_host, md_port = fronts['md'].split(':')
    
    td_ok = check_tcp(td_host, int(td_port))
    md_ok = check_tcp(md_host, int(md_port))
    
    print(f"  TD {fronts['td']}: {'✓ REACHABLE' if td_ok else '✗ UNREACHABLE'}")
    print(f"  MD {fronts['md']}: {'✓ REACHABLE' if md_ok else '✗ UNREACHABLE'}")
    
    if td_ok and md_ok:
        reachable_env = env_name

print("\n" + "=" * 60)
if reachable_env:
    fronts = HONGYUAN_FRONTS[reachable_env]
    print(f"Recommended: {reachable_env}")
    print(f"CTP_TD_FRONT=tcp://{fronts['td']}")
    print(f"CTP_MD_FRONT=tcp://{fronts['md']}")
else:
    print("No reachable Hongyuan environment found!")
