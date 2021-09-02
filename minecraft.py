import threading
import time
from subprocess import Popen, PIPE


def main():
    mc = Popen(["java", "-jar", "server.jar", "nogui"],
               stdin=PIPE, stdout=PIPE, bufsize=1, universal_newlines=True)

    output = threading.Thread(target=stdout, args=(mc,))
    output.start()

    input = threading.Thread(target=rawInput, args=(mc,))
    input.start()

    time.sleep(5)

    for i in range(10):
        communicate(mc, "/say Hi from Main Function")
        time.sleep(10)


def terminate(mc, output, input):
    communicate(mc, "stop")

    time.sleep(10)

    mc.terminate()
    output.do_run = False
    input.do_run = False


def stdout(mc):
    t = threading.current_thread()
    while getattr(t, "do_run", True):
        line = mc.stdout.readline()
        if line:
            print(line.strip())


def rawInput(mc):
    t = threading.current_thread()
    while getattr(t, "do_run", True):
        message = input("> ")
        mc.stdin.write("%s\n" % message)


def communicate(mc, message):
    print(message)
    mc.stdin.write("%s\n" % message)


if __name__ == "__main__":
    main()
