#!/usr/bin/python
# Copyright 2012 Bruno Gonzalez
# This software is released under the GNU AFFERO GENERAL PUBLIC LICENSE (see agpl-3.0.txt or www.gnu.org/licenses/agpl-3.0.html)
import threading
import time
from log import info, error
from catch_them_all import catch_them_all
from Queue import Queue

from oyoyo.client import IRCClient
from oyoyo.cmdhandler import DefaultCommandHandler
from message import Message

import binascii

class Handler(DefaultCommandHandler):
    # Handle messages (the PRIVMSG command, note lower case)
    @catch_them_all
    def privmsg(self, nick_full, chan, msg):
        try:
            msg = unicode(msg, "utf-8")
        except UnicodeDecodeError:
            try:
                msg = unicode(msg, "latin-1")
            except UnicodeDecodeError:
                hexa = binascii.hexlify(msg)
                error("Could not decode message: binascii.unhexlify(\"%s\")" %hexa)
                raise
        m = Message("irc", nick_full, chan, msg)
        self.irc_interface.msg_handler(m)
    def set_irc_interface(self, irc_interface):
        self.irc_interface = irc_interface
    @catch_them_all
    def join(self, nick_full, channel):
        self.irc_interface.joined(channel)
    @catch_them_all
    def part(self, nick_full, channel):
        self.irc_interface.parted(channel)
    @catch_them_all
    def kick(self, kicker, channel, nick, reason):
        self.irc_interface.parted(channel)

class IRCInterface(threading.Thread):
    def __init__(self, server, port, nick, owner, channels, msg_handler, stopped_handler):
        threading.Thread.__init__(self)
        self.must_run = True
        self.connected = False
        self.server_spamcheck = False
        self.spamcheck_enabled = True
        self.msg_handler = msg_handler
        self.stopped_handler = stopped_handler
        self.nick = nick
        self.host = server
        self.port = port
        self.channels = channels
	self.owner = 'Owner:'+owner+''
        self.send_queue = Queue()
        self.channels_joined = {}
        for c in self.channels:
            self.channels_joined[c] = False
        self.cli = IRCClient(Handler, host=self.host, port=self.port, nick=self.nick, connect_cb=self.connect_callback, real_name=self.owner)
        self.cli.command_handler.set_irc_interface(self)
    @catch_them_all
    def connect_callback(self, cli):
        self.server_connected = True
    def pending_channels(self):
        result = True
        for k,v in self.channels_joined.items():
            if not v:
                result = False
                break
        return result
    def joined(self, channel):
        self.channels_joined[channel] = True
        info(2, "Joined channel %s" %channel)
    def parted(self, channel):
        self.channels_joined[channel] = False
        info(2, "Left channel %s" %channel)
        if self.must_run:
            self.join_channels()
    def connect(self):
        info(2, "Connecting to server")
        self.server_connected = False
        self.conn = self.cli.connect()
        while not self.server_connected:
            if not self.must_run:
                raise Exception("Must stop")
            try:
                self.conn.next()
            except Exception, e:
                error("Problems while connecting to IRC server: %s" %e)
                self.stop()
                self.disconnected()

        info(2, "Connected to server")
	info(3, "Setting Botmode on IRC queue")
	self.send_queue.put("MODE %s +B" %self.nick)
    def next(self):
        try:
            self.conn.next()
        except Exception, e:
            time.sleep(0.05)
            error("Couldn't process connection: %s" %e)
            del self.conn
            self.connect()
    def join_channels(self):
		if self.server_connected == True and self.server_spamcheck == True:
			for c in self.channels:
				if not c in self.channels_joined or self.channels_joined[c] == False:
					info(3, "Joining channel %s" %c)
					self.cli.send("JOIN", c)
				while self.pending_channels():
					if not self.must_run:
						raise Exception("Must stop")
					self.conn.next()
    @catch_them_all
    def run(self):
        self.must_run = True
        info(2, "%s connecting to %s:%s" %(self.nick, self.host, self.port))
        self.connect()
        if self.spamcheck_enabled == 0:
	    self.join_channels()
        while not self.pending_channels():
            if not self.must_run:
                raise Exception("Must stop")
            self.next()
        self.connected = True
        info(2, "%s connected to %s:%s" %(self.nick, self.host, self.port))
        while self.must_run:
            self.next()
            time.sleep(0.1)
            if not self.send_queue.empty():
                text = self.send_queue.get()
                info(4, (" >>> IRC %s" %text).encode("utf-8"))
                self.cli.send(text)
                time.sleep(0.5)
        self.cli.send("QUIT :I Quit")
        info(2, "%s disconnected from %s:%s" %(self.nick, self.host, self.port))
        self.disconnected()
    def disconnected(self):
        self.connected = False
        del self.conn
        self.stopped_handler()
        self.must_run = False
    def stop(self):
        self.must_run = False
    def send(self, channel, text):
        info(4, (" ->- IRC %s: %s" %(channel, text)).encode("utf-8"))
        msg = "PRIVMSG %s :%s" %(channel, text)
        self.send_queue.put(msg)
    def wait_connected(self):
        while not self.connected:
            if not self.must_run:
                raise Exception("IRC: bot does not intend to connect")
            time.sleep(0.1)
