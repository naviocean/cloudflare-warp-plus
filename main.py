import sys
import shutil
import os
import time
from warp import WARP
from pprint import pprint

script_version = '1.0.0'
window_title = f"WARP-PLUS-CLOUDFLARE By NaviOcean (version {script_version})"
os.system('title ' + window_title if os.name ==
          'nt' else 'PS1="\[\e]0;' + window_title + '\a\]") echo $PS1')
os.system('cls' if os.name == 'nt' else 'clear')


def progressBar():
    animation = ["[□□□□□□□□□□]", "[■□□□□□□□□□]", "[■■□□□□□□□□]", "[■■■□□□□□□□]", "[■■■■□□□□□□]",
                 "[■■■■■□□□□□]", "[■■■■■■□□□□]", "[■■■■■■■□□□]", "[■■■■■■■■□□]", "[■■■■■■■■■□]"]
    progress_anim = 0
    save_anim = animation[progress_anim % len(animation)]
    percent = 0
    while True:
        for i in range(10):
            percent += 1
            sys.stdout.write(
                f"\r[+] Waiting response...  " + save_anim + f" {percent}%")
            sys.stdout.flush()
            time.sleep(0.075)
        progress_anim += 1
        save_anim = animation[progress_anim % len(animation)]
        if percent == 100:
            sys.stdout.write("\r[+] Request completed... [■■■■■■■■■■] 100%")
            break


if __name__ == "__main__":
    if shutil.which("wg") == None:
        print("Error: 'wg' must be installed and added to PATH")
        print("More information: https://www.wireguard.com/install/")
        sys.exit(1)

    print("  _      ____  _     _  ____  ____  _____ ____  _     ")
    print(" / \  /|/  _ \/ \ |\/ \/  _ \/   _\/  __//  _ \/ \  /|")
    print(" | |\ ||| / \|| | //| || / \||  /  |  \  | / \|| |\ ||")
    print(" | | \||| |-||| \// | || \_/||  \_ |  /_ | |-||| | \||")
    print(" \_/  \|\_/ \|\__/  \_/\____/\____/\____\\_/ \|\_/  \|")
    print("                                                      ")
    print("[+] ABOUT SCRIPT:")
    print("[-] With this script, you can getting unlimited GB on Warp+.")
    print(f"[-] Version: {script_version}")
    account_id: str
    while True:
        print("\r[-] 1. Create WireGuard configuration & buff data :")
        print("\r[-] 2. Buff data with ID only:\n")
        referrer = input("\r[+] Enter your selection (1|2):").lower()
        if referrer == '2':
            account_id = input("\r[+] Enter account ID:")
        if referrer in ['1', '2']:
            break

    wa = WARP()
    if referrer == '1':
        print(f"Getting configuration...")
        account_id = wa.createConfig()

    g = 0
    b = 0
    while True:
        sys.stdout.write("\r[+] Sending request...   [□□□□□□□□□□] 0%")
        sys.stdout.flush()
        result = wa.buffData(account_id)
        if result == 200:
            g += 1
            progressBar()
            print(f"\n[-] WORK ON ID: {referrer}")
            print(f"[:)] {g} GB has been successfully added to your account.")
            print(f"[#] Total: {g} Good {b} Bad")
            for i in range(18, 0, -1):
                sys.stdout.write(
                    f"\r[*] After {i} seconds, a new request will be sent.")
                sys.stdout.flush()
                time.sleep(1)
        else:
            b += 1
            print("[:(] Error when connecting to server.")
            print(f"[#] Total: {g} Good {b} Bad")
            for i in range(10, 0, -1):
                sys.stdout.write(f"\r[*] Retrying in {i}s...")
                sys.stdout.flush()
                time.sleep(1)
