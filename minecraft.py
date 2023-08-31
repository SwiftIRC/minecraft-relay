import threading
import time
from subprocess import Popen, PIPE
import re


class Minecraft():
    irc = None
    mc = None
    output = None
    input = None
    thread_lock = None
    players = []

    def set_thread_lock(self, lock):
        self.thread_lock = lock

    def run(self):
        self.mc = Popen(["java", "-Xmx15512m", "-jar", "server.jar", "nogui"],
                        stdin=PIPE, stdout=PIPE, bufsize=1, universal_newlines=True)

        self.output = threading.Thread(target=self.stdout)
        self.output.start()

        self.input = threading.Thread(target=self.rawInput)
        self.input.start()

    def stdout(self):
        while True:
            line = self.mc.stdout.readline()
            if line:
                output = line.strip()
                print(output)

                join = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): (\S+) (\(formerly known as \S+\) )?joined the game", output)

                part = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): (\S+) left the game", output)

                advancement = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): (\S+ has (made the advancement|completed the challenge|has reached the goal).*)", output)

                privmsg = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): (?:\[Not Secure\])? ?(?!<Server>)(<[^>]+> (.*)|\* (.*)|[^:\[\]*/]+)$", output)

                if join:
                    nick = join.group(1)
                    if ';' in nick:
                        nick = nick[10:]
                    self.irc.privmsg(
                        "#minecraft", "--> {} {}".format(nick, join.group(2) if join.group(2) != None else ''))
                    self.players.append(nick)
                elif part:
                    nick = part.group(1)
                    if ';' in nick:
                        nick = nick[10:]
                    self.irc.privmsg(
                        "#minecraft", "<-- " + nick)
                    self.players.remove(nick)
                elif advancement:
                    self.irc.privmsg(
                        "#minecraft", advancement.group(1))
                elif privmsg:
                    if not privmsg.group(1).startswith('UUID of player '):
                        self.irc.privmsg("#minecraft", privmsg.group(1))

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

    def get_players(self):
        return self.players
