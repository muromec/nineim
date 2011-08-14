import sys, os

import xmppony
import rbus

kw = {
        "user": os.getenv("USER"),
}

bus = rbus.RbusRoot("unix!/tmp/ns.%(user)s/nineim" % kw)
bus.children_types = [ "roster", "chat" ]

jid, passwd = sys.argv[1:3]
username, host = jid.split("@")

class prop(property):
    RBUS_PROP = True

class Client(xmppony.Client):
    chats = {}   # FIXME: global

    def message(self, conn, mess):
        text=mess.getBody()
        user=mess.getFrom()

        chat = self.get_chat(user)

        bus.put_event("msg %s" % (user,))


    def get_chat(self, jid):

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
        self._count = 0

        self.client = client

    @prop
    def jid(self):
        return self._jid

    @prop
    def count(self):
        self.send("increment %d" % self._count)
        self._count += 1

        return str(self._count)

    def send(self, text):
        message = xmppony.Message(self._jid, text)
        message.setAttr('type', 'chat')

        self.client.send(message)


client = Client(host, debug=None)
client.connect(server=(host, 5223))
client.auth(username, passwd, 'nineim')
client.sendInitPresence()

client.RegisterHandler('message', client.message)

while True:
    client.Process()
    bus.run()
