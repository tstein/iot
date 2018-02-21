#!/usr/bin/env python3

from argparse import ArgumentParser
from sys import exit, stdout
import re

import bs4
import requests


SCRIPT_CAPACITY = 127


class Switch():
    def __init__(self, host, user, passwd, timeout, attempts):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.timeout = timeout
        self.attempts = attempts

    def auth(self):
        return (self.user, self.passwd)


def load_script(script_path):
    with open(script_path, "r") as script:
        raw_lines = script.readlines()

    if len(raw_lines) > SCRIPT_CAPACITY:
        msg = """ERROR: Script has {lines} lines, but the switch can only accept
            {max_lines}."""
        print(msg.format(lines=len(raw_lines), max_lines=SCRIPT_CAPACITY))
        exit(255)

    def clean(line):
        return re.sub("#.*", "", line).strip()

    script_lines = [clean(l) for l in raw_lines]

    # Pad the script with ENDs.
    for _ in range(len(script_lines), SCRIPT_CAPACITY):
        script_lines.append("END")

    return script_lines


def read_script(switch):
    url = "http://{host}/script.htm".format(host=switch.host)
    attempts = 0
    while attempts < switch.attempts:
        try:
            r = requests.get(url, auth=switch.auth(), timeout=switch.timeout)
            break
        except (ConnectionResetError, requests.exceptions.ConnectTimeout):
            attempts += 1

    if r.status_code != 200:
        msg = "\nERROR: Got a {code} trying to POST to {url} as {user}:{passwd}."
        print(msg.format(
            code=r.status_code,
            url=r.url,
            user=switch.user,
            passwd=switch.passwd))
        if ("SECURITY LOCKOUT" in r.text):
            print()
            print("Additionally, the switch has entered security lockout mode.")
            print("Please wait for the lockout to expire or reboot the switch.")
        exit(255)

    soup = bs4.BeautifulSoup(r.text, "html.parser")
    # The script listing should be the last table.
    script_table = soup.find_all("table")[-1]
    if not "Script listing" in script_table.text:
        print("\nSwitch UI didn't have a script in the expected place.")
        print("""This may indicate that the UI changed and this program needs
        an update.""")
        exit(255)

    try:
        # Throw away the header.
        script_trs = script_table.find_all('tr')[1:]
        script_tds = [tr.find_all('td')[0:2] for tr in script_trs]
        script_pairs = [(int(l.text), r.find('tt').text) for l, r in script_tds]

        # One more sanity check.
        assert([l for l, _ in script_pairs] == list(range(1, 128)))
    except Exception as e:
        print("""\nSwitch UI appears to have a script listing, but it wasn't in the expected format.""")
        print("""This may indicate that the UI changed and this program needs an update.""")
        print("{}: {}".format(type(e), e))
    script = [r for _, r in script_pairs]
    return script


"""
There's no API to read script lines for machine consumption. We get the same
info by scraping the UI, but need to account for clarifying text appended to
some statements.
"""
def line_equal(expected, actual):
    e_tokens = expected.split(" ")
    a_tokens = actual.split(" ")

    if e_tokens[0] == "SLEEP":
        if e_tokens[0:2] == a_tokens[0:2]:
            return True
    else:
        return expected == actual


def verify_script(expected, switch):
    stdout.write("Verifying that the switch has the new script... ")
    actual = read_script(switch)
    for i, (e, a) in enumerate(zip(expected, actual)):
        if not line_equal(e, a):
            print("\nVerification first failed on line {}: wrote '{}' but the switch has '{}'"
                .format(i, e, a))
            return False
    print("done.")
    return True


"""
Some APIs are exposed on /script and others on /script.cgi.
"""
def switch_script_post(switch, params, cgi=False):
    url = "http://{host}/script{cgi}".format(
            host=switch.host,
            cgi=".cgi" if cgi else "")
    attempts = 0
    r = None
    while attempts < switch.attempts:
        try:
            r = requests.post(
                    url,
                    auth=switch.auth(),
                    data=params,
                    timeout=switch.timeout)
            break
        except (ConnectionResetError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError):
            attempts += 1

    if r.status_code != 200:
        msg = "\nERROR: Got a {code} trying to POST to {url} as {user}:{passwd}."
        print(msg.format(
            code=r.status_code,
            url=r.url,
            user=switch.user,
            passwd=switch.passwd))
        if ("SECURITY LOCKOUT" in r.text):
            print()
            print("Additionally, the switch has entered security lockout mode.")
            print("Please wait for the lockout to expire or reboot the switch.")
        exit(255)

def stop_scripting(switch):
    stdout.write("\rStopping scripting... ")
    params = {"stop": ""}
    switch_script_post(switch, params, cgi=True)
    stdout.write("done.\n")


def start_scripting(switch, line_num):
    stdout.write("\rStarting a thread at line {num}... ".format(num=line_num))
    params = {"run{:03}".format(line_num): "run"}
    switch_script_post(switch, params)
    stdout.write("done.\n")


def write_script(script, switch):
    def write_line(switch, line_num, text):
        params = {"edit{:03}".format(line_num): text}
        switch_script_post(switch, params)

    # Scripts are 1-indexed.
    enumerated_lines = [(i + 1, l) for i, l in enumerate(script)]

    stdout.write("\rWriting script...   0%")
    for line_num, line in enumerated_lines:
        progress = int(round(line_num / SCRIPT_CAPACITY, 2) * 100)
        stdout.write(
                "\rWriting script... {progress:3d}%".format(progress=progress))
        write_line(switch, line_num, line)

    stdout.write("\rWriting script... 100%\n")


def main():
    parser = ArgumentParser(
        description="""Write a script to a DLI Web Power Switch.

This program will stop all threads on the switch, overwrite the entire script
stored on it, and start a thread at the first line of your script.

If writing the script is interrupted, your switch's script may be left in an
inconsistent state and will not be running. You can safely run this again
to fix this and get scripting running again.""")
    parser.add_argument("MODE", type=str,
        help="'read' or 'write'")
    parser.add_argument("HOST", type=str,
        help="hostname or IP address of a DLI Web Power Switch")
    parser.add_argument("SCRIPT", type=str, nargs="?",
        help="""file containing a DLI-flavored Basic script (write mode
        only)""")

    parser.add_argument("--user", type=str, default="admin",
        help="username to provide to the switch (default: admin)")
    parser.add_argument("--pass", type=str, default="1234", dest="passwd",
            help="password to provide to the switch (default: 1234)")
    parser.add_argument("--timeout", type=int, default=3,
        help = """maximum number of seconds to wait for any single request
            (default: 3)""")
    parser.add_argument("--attempts", type=int, default=3,
        help="""number of attempts to make on any single request before
            aborting the entire run (default: 3)""")
    args = parser.parse_args()
    switch = Switch(
            args.HOST, args.user, args.passwd,
            args.timeout, args.attempts)

    if args.MODE == "read":
        if args.SCRIPT:
            print("Don't give me a file in read mode.")
            exit(2)

        script = read_script(switch)
        print("\n".join(script))
        exit(0)
    elif args.MODE == "write":
        script = load_script(args.SCRIPT)
        stop_scripting(switch)
        write_script(script, switch)
        if verify_script(script, switch):
            start_scripting(switch, 1)
            exit(255)
    else:
        print("""Given invalid mode '{}'. (must be 'read' or 'write')"""
                .format(args.MODE))
        exit(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(255)
