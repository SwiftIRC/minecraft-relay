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

    def stdout(self):
        while True:
            line = self.mc.stdout.readline()
            if line:
                output = line.strip()
                print(output)

                privmsg = re.match(
                    r"\[[^]]+\] \[Server thread/INFO\]: (<[^>]+> (.*)|\* (.*))", output)

                join = re.match(
                    r"\[[^]]+\] \[Server thread/INFO\]: (\S+) joined the game", output)

                part = re.match(
                    r"\[[^]]+\] \[Server thread/INFO\]: (\S+) left the game", output)

                if privmsg:
                    self.irc.privmsg("#minecraft", privmsg.group(1))
                elif join:
                    self.irc.privmsg(
                        "#minecraft", "--> " + join.group(1))
                elif part:
                    self.irc.privmsg(
                        "#minecraft", "<-- " + part.group(1))

    def rawInput(self):
        while True:
            message = input("> ")
            self.communicate(message)

    def communicate(self, message):
        print(message)
        self.mc.stdin.write("%s\n" % message)

    def privmsg(self, message):
        self.communicate("say %s" % message)

    def set_irc(self, irc):
        self.irc = irc
