#!/usr/bin/env python3

import irc.bot
import re
import json


class IRC(irc.bot.SingleServerIRCBot):
    thread_lock = None
    running = True

    config = None
    connection = None
    mc = None

    def __init__(self):
        with open("config.json") as json_data_file:
            self.config = json.load(json_data_file)

        irc.client.ServerConnection.buffer_class.encoding = "latin-1"
        irc.bot.SingleServerIRCBot.__init__(self, [
            (self.config['network'],
             self.config['port'])],
            self.config['nick'],
            self.config['realname'])

    def set_mc(self, mc):
        self.mc = mc

    def set_thread_lock(self, lock):
        self.thread_lock = lock

    def close(self):
        self.running = False
        self.connection.quit(self.config['quitmsg'])

    def privmsg(self, target, message):
        self.connection.privmsg(target, message.strip())

    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")

    def on_welcome(self, connection, event):
        self.connection = connection

        connection.join(self.config['channel'])

    def on_pubmsg(self, connection, event):
        self.handleMessage(connection, event, None)

    def on_action(self, connection, event):
        self.handleMessage(connection, event, "* ")

    def handleMessage(self, connection, event, prefix):
        if (event.target.lower() == "#minecraft"):
            with self.thread_lock:
                message = self.escape_at_sign(event.arguments[0].strip())
                if prefix is None:
                    message = "<{:s}> {:s}".format(event.source.nick, message)
                else:
                    message = "{:s} {:s} {:s}".format(
                        prefix, event.source.nick, message)
                self.mc.privmsg(self.strip_colors(message))

                if re.match(r'[!@.+-](players|online)', message):
                    self.privmsg(event.target, self.mc.get_players())

    def strip_colors(self, message):
        return re.sub(r'\x03(?:\d{1,2}(?:,\d{1,2})?)?|[\x02\x09\x13\x0f\x15\x1f\x16]', '', message)

    def escape_at_sign(self, message):
        return message.replace("@", "@\\")

    def run(self):
        self.start()
