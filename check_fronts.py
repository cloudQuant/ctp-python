#!/usr/bin/env python
"""Check which CTP front addresses are reachable."""
import socket
import sys

# 第一套环境（交易时段）
FRONTS_SET1 = [
    ("182.254.243.31:30001", "TD", "第一组"),
    ("182.254.243.31:30011", "MD", "第一组"),
    ("182.254.243.31:30002", "TD", "第二组"),
    ("182.254.243.31:30012", "MD", "第二组"),
    ("182.254.243.31:30003", "TD", "第三组"),
    ("182.254.243.31:30013", "MD", "第三组"),
]

# 第二套环境（7x24）
FRONTS_SET2 = [
    ("182.254.243.31:40001", "TD", "7x24"),
    ("182.254.243.31:40011", "MD", "7x24"),
]

def check_tcp(host, port, timeout=3):
    """Check if TCP port is reachable."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception as e:
        return False

def main():
    print("=" * 60)
    print("CTP Front Address Reachability Check")
    print("=" * 60)
    
    reachable_set1_td = []
    reachable_set1_md = []
    reachable_set2_td = []
    reachable_set2_md = []
    
    print("\n第一套环境（交易时段）:")
    for addr, front_type, group in FRONTS_SET1:
        host, port = addr.split(":")
        port = int(port)
        ok = check_tcp(host, port)
        status = "✓ REACHABLE" if ok else "✗ UNREACHABLE"
        print(f"  {group} {front_type}: {addr} -> {status}")
        if ok:
            if front_type == "TD":
                reachable_set1_td.append(addr)
            else:
                reachable_set1_md.append(addr)
    
    print("\n第二套环境（7x24）:")
    for addr, front_type, group in FRONTS_SET2:
        host, port = addr.split(":")
        port = int(port)
        ok = check_tcp(host, port)
        status = "✓ REACHABLE" if ok else "✗ UNREACHABLE"
        print(f"  {group} {front_type}: {addr} -> {status}")
        if ok:
            if front_type == "TD":
                reachable_set2_td.append(addr)
            else:
                reachable_set2_md.append(addr)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    # 推荐配置
    if reachable_set2_td and reachable_set2_md:
        print(f"\n推荐使用第二套环境（7x24）:")
        print(f"  TD: tcp://{reachable_set2_td[0]}")
        print(f"  MD: tcp://{reachable_set2_md[0]}")
    elif reachable_set1_td and reachable_set1_md:
        print(f"\n推荐使用第一套环境:")
        print(f"  TD: tcp://{reachable_set1_td[0]}")
        print(f"  MD: tcp://{reachable_set1_md[0]}")
    else:
        print("\n警告: 没有可用的CTP前置地址!")
    
    # 输出为环境变量格式
    print("\n" + "=" * 60)
    print("Environment variables for .env:")
    print("=" * 60)
    if reachable_set2_td and reachable_set2_md:
        print(f"CTP_TD_FRONT=tcp://{reachable_set2_td[0]}")
        print(f"CTP_MD_FRONT=tcp://{reachable_set2_md[0]}")
    elif reachable_set1_td and reachable_set1_md:
        print(f"CTP_TD_FRONT=tcp://{reachable_set1_td[0]}")
        print(f"CTP_MD_FRONT=tcp://{reachable_set1_md[0]}")
    else:
        print("# No reachable fronts found!")

if __name__ == "__main__":
    main()
