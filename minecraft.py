import threading
import time
from subprocess import Popen, PIPE
import re


class Minecraft():
    irc = None
    mc = None
    output = None
    input = None

    def run(self):
        self.mc = Popen(["java", "-jar", "server.jar", "nogui"],
                        stdin=PIPE, stdout=PIPE, bufsize=1, universal_newlines=True)

        self.output = threading.Thread(target=self.stdout)
        self.output.start()

        input = threading.Thread(target=self.rawInput)
        input.start()

    def terminate(self):
        self.communicate("stop")

        time.sleep(10)

        self.mc.terminate()
        self.output.do_run = False
        self.input.do_run = False

    def stdout(self):
        t = threading.current_thread()
        while getattr(t, "do_run", True):
            line = self.mc.stdout.readline()
            if line:
                output = line.strip()
                print(output)

                match = re.match(
                    r"\[[^]]+\] \[Server thread/INFO\]: (<[^>]+> .*|\* .*)", output)

                if match:
                    self.irc.privmsg("#minecraft", match.group(1))

    def rawInput(self):
        t = threading.current_thread()
        while getattr(t, "do_run", True):
            message = input("> ")
            if message == "stop":
                self.terminate()
            else:
                self.communicate(message)

    def communicate(self, message):
        print(message)
        self.mc.stdin.write("%s\n" % message)

    def privmsg(self, message):
        self.communicate("say %s" % message)

    def set_irc(self, irc):
        self.irc = irc
