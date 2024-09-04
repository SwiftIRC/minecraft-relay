import json
from subprocess import Popen, PIPE, check_output
import random
import re
from datetime import datetime
import time
import threading
from mcfunctionhelper import getPlayerIdByName


class Minecraft:
    irc = None
    mc = None
    output = None
    input = None
    thread_lock = None
    vc_ctf_handler = None
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

    def parseNick(self, nick):
        if ";" in nick:
            m = re.match(
                r"(?:.+?\d+m)?([^?\x1b]+)(?:\?.+?\d+m)?",
                nick,
            )
            if m:
                nick = m.group(1)
        elif ";" in nick:
            nick = nick[10:]
        return nick

    def stdout(self):
        while True:
            try:
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
                        r"(?:\[[^]]+\] \[Server thread/INFO\]|\[\d+:\d+:\d+ INFO]): ((\S+ has (?:made the advancement|completed the challenge|reached the goal)).*)",
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
                        nick = self.parseNick(join.group(1))
                        self.irc.privmsg(
                            "#minecraft",
                            "--> {} {}".format(
                                nick, join.group(2) if join.group(2) != None else ""
                            ),
                        )
                        self.players.append(nick)
                    elif part:
                        nick = self.parseNick(part.group(1))
                        self.irc.privmsg("#minecraft", "<-- " + nick)
                        self.players.remove(nick)
                    elif advancement:
                        adv = advancement.group(1)
                        if ";" in adv:
                            new_advancement = re.match(r".+(\[[^]]+\]).+", adv)
                            adv = " ".join(
                                [advancement.group(2), new_advancement.group(1)]
                            )
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

                    elif privmsg:
                        if (
                            not privmsg.group(1).startswith("UUID of player ")
                            and not (
                                privmsg.group(1).startswith("Player profile key for ")
                                and privmsg.group(1).endswith(" has expired!")
                            )
                            and not privmsg.group(1).startswith("Teleported ")
                            and not privmsg.group(1).startswith("Changed the block at")
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
                        elif cmd in [
                            "!VC_CTF_5",
                            "!VC_CTF_10",
                            "!VC_CTF_15",
                            "!VC_CTF_20",
                        ]:
                            if self.vc_ctf_handler != None:
                                self.vc_ctf_handler = None

                            duration = int(cmd.split("_")[-1])
                            self.vc_ctf_handler = threading.Thread(
                                target=self.vc_ctf, args=(duration,)
                            )
                            self.vc_ctf_handler.start()

                    elif score:
                        objective = score.group(1)
                        player = score.group(2)
                        value = score.group(3)

                        if objective == "tentacle_tower_elevator":
                            with open("data/tentacle_tower_elevator.json", "r") as f:
                                data = f.read()
                                j = json.loads(data)
                                default_coord = j["floors"]["1"]
                                if int(value) < 0:
                                    player_id = getPlayerIdByName(player)
                                    floor_number = None
                                    for tenant in j:
                                        if int(tenant["player"]) == int(player_id):
                                            floor_number = int(tenant["floor"])
                                            continue
                                    floor_coords = (
                                        j["floors"][str(floor_number)]
                                        if j["floors"][str(floor_number)]
                                        else default_coord
                                    )

                                else:
                                    floor_coords = j.get("floors", {}).get(
                                        value, default_coord  # default to main floor
                                    )
                                self.communicate(
                                    "execute at {} in minecraft:overworld run tp @a[distance=..3] {}".format(
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
                        elif objective == "tentacle_tower_lease":
                            if getPlayerIdByName(player) != None:
                                self.communicate(
                                    'give {} written_book{pages:[\'["",{"text":"Squid Towers","bold":true,"underlined":true,"color":"blue"},{"text":" Lease Agreement","color":"reset","bold":true,"underlined":true},{"text":"\\n\\n","color":"reset"},{"text":"Tenant Name:","bold":true},{"text":" ","color":"reset"},{"selector":"{}"},{"text":"\\n\\n"},{"text":"Leased Space:","bold":true},{"text":" [Room #]\\n\\n","color":"reset"},{"text":"P.O. Box:","bold":true},{"text":" [#]","color":"reset"}]\',\'["",{"text":"You have been invited to stay at the luxurious "},{"text":"Squid Towers","bold":true,"color":"blue"},{"text":" condos in the beautiful new city of ","color":"reset"},{"text":"Squidelphia","bold":true,"color":"blue"},{"text":"!\\n\\nAs a VIP, your rent has been comped.\\n\\nYou will be given a condo and a P.O. Box.","color":"reset"}]\',\'["",{"text":"1. You "},{"text":"may not","bold":true},{"text":" modify the exterior walls or windows.\\n\\n2. You ","color":"reset"},{"text":"may change","bold":true},{"text":" the floors, ceilings, and room interiors. You may add walls.\\n\\n3. No contract. You may leave at any time.","color":"reset"}]\',\'["",{"text":"Enjoy your stay at "},{"text":"Squid Towers","bold":true,"color":"blue"},{"text":"!\\n\\n","color":"reset"},{"text":"Address","bold":true},{"text":":\\n","color":"reset"},{"text":"X","bold":true},{"text":": -7627,\\n","color":"reset"},{"text":"Y","bold":true},{"text":": 54,\\n","color":"reset"},{"text":"Z","bold":true},{"text":": -2419\\n\\n- Cult of Squid","color":"reset"}]\'],title:"Squid Towers Lease Agreement",author:"Cult of Squid",display:{Lore:["Squid Towers lease agreement in Squidelphia. Contains condo information."]}}'.format(
                                        player,
                                        player,
                                        int(getPlayerIdByName(player)) + 101,
                                    )
                                )
                            else:
                                self.communicate(
                                    'tellraw {} ["",{"text":"Player not found","color":"red"}]'.format(
                                        player
                                    )
                                )
            except Exception as e:
                print(e)
                pass

    def rawInput(self):
        while True:
            message = input("> ")
            self.communicate(message)

    def communicate(self, message):
        print(message)
        self.mc.stdin.write("%s\n" % message)

    def privmsg(self, message):
        self.communicate("say %s" % message)

    def tell(self, target, message):
        self.communicate("tell %s %s" % (target, message))

    def set_irc(self, irc):
        self.irc = irc

    def get_players(self):
        return self.players

    def fortune(self):
        return check_output(["/usr/games/fortune", "-s"])

    def vc_ctf(self, duration=5):
        timestamp = lambda: datetime.now().time()
        seconds = lambda t: (t.hour * 60 + t.minute) * 60 + t.second

        end = seconds(timestamp()) + duration * 60

        th = self.vc_ctf_handler

        while seconds(timestamp()) <= end:
            if (
                self.vc_ctf_handler != None
                and self.vc_ctf_handler.native_id != th.native_id
            ):
                return
            time.sleep(1)
            now = seconds(timestamp())
            remaining = end - now
            if not remaining % 60:
                d = int(remaining / 60)
                self.tell(
                    "@a[team=VC_CTF_1]",
                    "%d min%s remaining in the CTF" % (d, "s" if d != 1 else ""),
                )
                self.tell(
                    "@a[team=VC_CTF_2]",
                    "%d min%s remaining in the CTF" % (d, "s" if d != 1 else ""),
                )
                self.tell(
                    "@a[team=VC_CTF_3]",
                    "%d min%s remaining in the CTF" % (d, "s" if d != 1 else ""),
                )

        self.communicate("tp @a[team=VC_CTF_1] -12035 71 800")
        self.communicate("tp @a[team=VC_CTF_2] -12035 71 800")
        self.communicate("tp @a[team=VC_CTF_3] -12035 71 800")

        self.vc_ctf_handler = None
