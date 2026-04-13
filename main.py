import ctypes
import random
import string
import sys
import multiprocessing as mp
import requests
import os
import time

# --- 設定エリア ---
# GitHub SecretsからWebhook URLを取得（パブリック公開時の安全対策）
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

TARGETS = ['O.ccc.com/', 'O.cccco.jp'] # 100点
GREAT_PREFIX = 'O.ccc.com'             # 90点
GOOD_PREFIX = 'O.ccc'                  # 70点

# GHAの仕様（6時間で強制終了）を避けるため、5.5時間（19800秒）で安全に停止させる
MAX_DURATION = 19800 
start_time = time.time()
# ----------------

libc = ctypes.CDLL("libcrypt.so.1")
libc.crypt.restype = ctypes.c_char_p
libc.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
chars = string.ascii_letters + string.digits + '#./!'

def send_discord(message):
    if not WEBHOOK_URL:
        return
    try:
        # usernameを 'cbtrip' に上書きして送信
        requests.post(WEBHOOK_URL, json={"content": message, "username": "cbtrip"})
    except:
        pass

def make_trip(key):
    s = (key + 'HH')[1:3]
    salt = ''
    m = {0x3a:'A',0x3b:'B',0x3c:'C',0x3d:'D',0x3e:'E',0x3f:'F',0x40:'G',
         0x5b:'a',0x5c:'b',0x5d:'c',0x5e:'d',0x5f:'e',0x60:'f'}
    for c in s: salt += m.get(ord(c), c)
    res = libc.crypt(key.encode('utf-8'), salt[:2].encode('utf-8'))
    return res.decode('utf-8')[3:13] if res else ""

def worker(q):
    local_count = 0
    # 時間制限が来るまで回し続ける
    while time.time() - start_time < MAX_DURATION:
        key = ''.join(random.choices(chars, k=8))
        t = make_trip(key)

        if t in TARGETS:
            msg = f"🌈【100点：本命！】\nキー: #{key}\nトリップ: ◆{t}"
            send_discord(msg)
        elif t.startswith(GREAT_PREFIX):
            msg = f"💎【90点：ほぼ本命！】\nキー: #{key}\nトリップ: ◆{t}"
            send_discord(msg)
        elif t.startswith(GOOD_PREFIX):
            msg = f"✨【70点：テスト用】 #{key} -> ◆{t}"
            send_discord(msg)

        local_count += 1
        if local_count >= 10000:
            q.put(local_count)
            local_count = 0
    
    # 終了時に端数を返す
    q.put(local_count)

if __name__ == "__main__":
    if not WEBHOOK_URL:
        print("エラー: DISCORD_WEBHOOK_URLが設定されていません。")
        sys.exit(1)

    num_cores = mp.cpu_count()
    print(f"🏭 cbtrip工場稼働開始: CPU {num_cores} 基で探索します。")
    print(f"予定稼働時間: 5.5時間")

    q = mp.Queue()
    processes = [mp.Process(target=worker, args=(q,)) for _ in range(num_cores)]
    for p in processes: p.start()

    total_tried = 0
    try:
        # プロセスが生きている間ループ
        while any(p.is_alive() for p in processes):
            while not q.empty():
                total_tried += q.get()
                if total_tried % 1000000 == 0:
                    print(f"\r累計: {total_tried//10000}万回...", end="")
                    sys.stdout.flush()
            time.sleep(1)
            
    except KeyboardInterrupt:
        for p in processes: p.terminate()
        
    for p in processes: p.join()
    print(f"\n🛑 シフト終了。今回の累計は {total_tried} 回でした。次のシフトを待ちます。")
