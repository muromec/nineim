import sys, os

import xmppony
import rbus

kw = {
        "user": os.getenv("USER"),
}

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
            bus.put_event("chat %s" % (jid,))

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

        self.clients = []

        super(Nien, self).__init__(address=addr)

    def run(self):
        for client in self.clients:
            client.Process()

        super(Nien, self).run()

    def _get_ctl(self):
        return "NANI-NANI"

    def _set_ctl(self, val):
        args = val.strip().split(" ")
        cmd = args[0]

        handler = getattr(self, 'handle_%s' % cmd, None)

        if handler:
            handler(*args[1:])
        else:
            print 'ctl', val

    ctl = prop(_get_ctl, _set_ctl)


    def handle_connect(self, server):
        print 'connect to %s' % server


    def handle_chat(self, jid):
        print 'chat with %s' % jid
        client = self.clients[0]

        client.get_chat(jid)

    def handle_account(self, jid, pwd):
        print 'setup account %s with %s' % (jid, pwd)

        username, host = jid.split('@', 1)

        client = Client(host, debug=None)
        client.connect(server=(host, 5223))
        client.auth(username, pwd, 'nineim')
        client.sendInitPresence()

        client.RegisterHandler('message', client.message)

        self.clients.append(client)


bus = Nien()
bus.children_types = [ "roster", "chat" ]



while True:
    bus.run()
