from minecraft import Minecraft
from ircd import IRC
import threading


thread_lock = threading.Lock()


def main():
    mc = Minecraft()
    irc = IRC()

    mc.set_irc(irc)
    irc.set_mc(mc)

    mc.set_thread_lock(thread_lock)
    irc.set_thread_lock(thread_lock)

    th = threading.Thread(target=irc.run)

    th.start()

    mc.run()  # keep things running
    irc.run()


if __name__ == "__main__":
    main()
