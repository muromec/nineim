import sys, os

import xmppony
import rbus

kw = {
        "user": os.getenv("USER"),
}

jid, passwd = sys.argv[1:3]
username, host = jid.split("@")

class prop(property):
    RBUS_PROP = True

class Client(xmppony.Client):
    chats = {}   # FIXME: global

    def message(self, conn, mess):
        text=mess.getBody()
        if not text:
            return

        text = text.encode('utf8')

        user=mess.getFrom()

        chat = self.get_chat(user)

        bus.put_event(text, chat)


    def get_chat(self, jid):

        # FIXME:
        if not isinstance(jid, basestring):
            jid = jid.getStripped()

        chat = self.chats.get(jid)

        if not chat:
            chat = Chat(self, jid=jid)
            bus.put_event("new chat %s" % (jid,))

            bus.append_child(chat)

        self.chats[jid] = chat

        return chat


class Chat(object):
    RBUS_TYPE = "chat"

    def __init__(self, client, jid):
        self._jid = jid
        self.__name__ = jid

        self.client = client

    @prop
    def jid(self):
        return self._jid

    def send(self, text):
        message = xmppony.Message(self._jid, text)
        message.setAttr('type', 'chat')

        self.client.send(message)

    msg = prop(lambda self: "", send)

class Nien(rbus.RbusRoot):
    ADDR = "unix!/tmp/ns.%(user)s/nineim"

    def __init__(self):
        kw = {"user": os.getenv("USER")}
        addr = self.ADDR % kw

        super(Nien, self).__init__(address=addr)

    def _get_ctl(self):
        return "NANI-NANI"

    def _set_ctl(self, val):
        args = val.strip().split(" ")
        cmd = args[0]

        handler = getattr(self, 'handle_%s' % cmd, None)

        if handler:
            handler(*args[1:])

    ctl = prop(_get_ctl, _set_ctl)


    def handle_connect(self, server):
        print 'connect to %s' % server


bus = Nien()
bus.children_types = [ "roster", "chat" ]


client = Client(host, debug=None)
client.connect(server=(host, 5223))
client.auth(username, passwd, 'nineim')
client.sendInitPresence()

client.RegisterHandler('message', client.message)

while True:
    client.Process()
    bus.run()
