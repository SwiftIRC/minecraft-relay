from subprocess import Popen, PIPE, check_output
import random
import re
import threading
from mcfunctionhelper import getPlayerIdByName


class Minecraft:
    irc = None
    mc = None
    output = None
    input = None
    thread_lock = None
    players = []

    def set_thread_lock(self, lock):
        self.thread_lock = lock

    def run(self):
        self.mc = Popen(
            ["java", "-Xmx15512m", "-jar", "server.jar", "nogui"],
            stdin=PIPE,
            stdout=PIPE,
            bufsize=1,
            universal_newlines=True,
        )

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
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): (\S+) (\(formerly known as \S+\) )?joined the game",
                    output,
                )

                part = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): (\S+) left the game",
                    output,
                )

                advancement = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): ((\S+ has (?:made the advancement|completed the challenge|has reached the goal)).*)",
                    output,
                )

                objective = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): \S+\[@: Created new objective \[([^]]+)\]\]",
                    output,
                )

                score = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): \S+\[@: (?:Set|Added \d+ to) \[(\w+)\] for ([\w-]+) to (-?\d+)\]",
                    output,
                )

                trigger = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): (?:\[Not Secure\])? ?(?!<Server>)(<[^>]+> !(.*))$",
                    output,
                )

                privmsg = re.match(
                    r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): (?:\[Not Secure\])? ?(?!<Server>)(<[^>]+> (.*)|\* (.*)|[^:\[\]*/]+)$",
                    output,
                )

                if join:
                    nick = join.group(1)
                    if ";" in nick:
                        nick = nick[10:]
                    self.irc.privmsg(
                        "#minecraft",
                        "--> {} {}".format(
                            nick, join.group(2) if join.group(2) != None else ""
                        ),
                    )
                    self.players.append(nick)
                elif part:
                    nick = part.group(1)
                    if ";" in nick:
                        nick = nick[10:]
                    self.irc.privmsg("#minecraft", "<-- " + nick)
                    self.players.remove(nick)
                elif advancement:
                    adv = advancement.group(1)
                    if ";" in adv:
                        new_advancement = re.match(r".+(\[[^]]+\]).+", adv)
                        adv = " ".join([advancement.group(2), new_advancement.group(1)])
                    self.irc.privmsg("#minecraft", adv)
                elif trigger:
                    cmd = trigger.group(2)

                    if cmd.startswith("calc "):
                        equation = cmd[5:]

                        if re.match(r"^[0-9\+\-\*\/\(\)\. ]+$", equation):
                            try:
                                self.privmsg(str(eval(equation)))
                            except:
                                self.privmsg("Error")

                    # elif cmd == "register":

                elif privmsg:
                    if not privmsg.group(1).startswith("UUID of player ") and not (
                        privmsg.group(1).startswith("Player profile key for ")
                        and privmsg.group(1).endswith(" has expired!")
                    ):
                        self.irc.privmsg("#minecraft", privmsg.group(1))
                elif objective:
                    cmd = objective.group(1)

                    if cmd == "!fortune":
                        self.privmsg(
                            "[Fortune] {}".format(
                                self.fortune()
                                .decode("utf-8")
                                .replace("\n", " ")
                                .replace("\r", "")
                            )
                        )
                elif score:
                    objective = score.group(1)
                    player = score.group(2)
                    value = score.group(3)

                    if objective == "tentacle_tower_elevator":
                        with open("data/tentacle_tower_elevator.json", "r") as f:
                            data = f.read()
                            default_coord = data.floors["1"]
                            if value < 0:
                                player_id = getPlayerIdByName(player)
                                floor_number = None
                                for tenant in data:
                                    if tenant.player == player_id:
                                        floor_number = tenant.floor
                                        continue
                                floor_coords = (
                                    data.floors[str(floor_number)]
                                    if data.floors[str(floor_number)]
                                    else default_coord
                                )

                            else:
                                floor_coords = data.get("floors", {}).get(
                                    value, default_coord  # default to main floor
                                )
                            self.communicate(
                                "execute at {} in minecraft:overworld run tp @a[distance=..5] {}".format(
                                    player, floor_coords
                                )
                            )
                            self.communicate(
                                "execute at {} run function custom:buildings/elevator/ding".format(
                                    player
                                )
                            )

                            self.communicate(
                                "scoreboard players reset {} tentacle_tower_elevator".format(
                                    player
                                )
                            )

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

    def fortune(self):
        return check_output(["/usr/games/fortune", "-s"])
