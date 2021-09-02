#!/usr/bin/env python3

import irc.bot
import re


class IRC(irc.bot.SingleServerIRCBot):
    thread_lock = None
    running = True

    # config = None
    connection = None
    mc = None

    def __init__(self):
        irc.client.ServerConnection.buffer_class.encoding = "latin-1"
        irc.bot.SingleServerIRCBot.__init__(self, [
            ("fiery.swiftirc.net",
             6667)],
            "Minecraft",
            "Minecraft Relay")

        # self.config = config

    def set_mc(self, mc):
        self.mc = mc

    def set_thread_lock(self, lock):
        self.thread_lock = lock

    def close(self):
        self.running = False
        self.connection.quit("Adios!")

    def privmsg(self, target, message):
        self.connection.privmsg(target, message.strip())

    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")

    def on_welcome(self, connection, event):
        self.connection = connection

        connection.join("#minecraft")
        # ','.join([channel for channel in self.config['CHANNELS']]))

    def on_pubmsg(self, connection, event):
        if (event.target == "#minecraft"):
            with self.thread_lock:
                message = event.arguments[0].strip()
                message = "<{:s}> {:s}".format(event.source.nick, message)
                self.mc.privmsg(message)

    def on_action(self, connection, event):
        if (event.target == "#minecraft"):
            with self.thread_lock:
                message = event.arguments[0].strip()
                message = "* {:s} {:s}".format(event.source.nick, message)
                self.mc.privmsg(message)

    def run(self):
        self.start()

        if self.running:
            self.running = False
            ircd = IRC({"irc": self.config})
            ircd.set_mc(self.mc)
            self.mc.set_irc(ircd)
            ircd.set_thread_lock(self.thread_lock)
            ircd.run()
