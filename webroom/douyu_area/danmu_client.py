# coding=utf-8

import logging
import socket
import time
import uuid
import hashlib
import binascii
import re
import threading

DANMU_ADDR = ("danmu.douyutv.com", 8601)

class DanmuClient(object):

    def __init__(self, room, auth_dst_ip, auth_dst_port, username=None, password=None):
        self.auth_dst_ip = auth_dst_ip
        self.auth_dst_port = auth_dst_port
        self.room = room
        self.room_id = room["id"]
        self.auth_socket = None
        self.danmu_socket = None
        self.username = username or ""
        self.password = password or ""
        self.gid = 1
        self.live_stat = 0

    def init_socket(self):
        if self.auth_socket is None:
            # Init auth socket for login
            self.auth_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            socket_addr = (self.auth_dst_ip, self.auth_dst_port)
            self.auth_socket.connect(socket_addr)
            logging.info("auth socket connect:{}:{}".format(self.auth_dst_ip, self.auth_dst_port))


        if self.danmu_socket is None:
            # Init danmu socket. recev msg and send msg
            self.danmu_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.danmu_socket.connect(DANMU_ADDR)

    def connect_server(self):
        """Connect server

        1.Send `type@=loginreq` request;
        2.Send `type@=qrl` request;
        3.Send `type@=qtlnq` request;
        4.Send `type@=keylive` request;
        """
        # Send `type@=loginreq` request.
        timestamp = int(time.time())
        devid = str(uuid.uuid4()).replace("-","")
        room_id = self.room["id"]
        vk = hashlib.md5(str(timestamp) + "7oE9nPEG9xXV69phU31FYCLUagKeYtsF" + devid).hexdigest()
        login_data = "type@=loginreq/username@=/ct@=0/password@=/roomid@={}/devid@={}/rt@={}/vk@={}/ver@=20150929/ltkid@=/biz@=/stk@=/".format(room_id, devid, timestamp, vk)

        self.send_data(self.auth_socket, login_data)
        msg = self.auth_socket.recv(4000)
        logging.debug("auth login recv:{}".format(msg))

        if "live_stat@=0" in msg:
            logging.info(u"当前房间离线")
            self.live_stat = 0
        else:
            logging.info(u"当前房间在线")
            self.live_stat = 1
            result = self.parse_regex("/username@=(.*?)/nickname", msg)
            if result is not None:
                self.username = result[0]

            # recv msg to get `gid` value
            msg = self.auth_socket.recv(4000)
            logging.debug("auth login recv:{}".format(msg))
            result = self.parse_regex(r'/gid@=(\d+)/', msg)
            if result is not None:
                self.gid = result[0]

            # Send `type@=qrl` request.
            qrl_data = "type@=qrl/rid@={}/et@=0/".format(room_id)
            self.send_data(self.auth_socket, qrl_data)

            # Send `type@=qtlnq` request.
            qtlnq_data = "type@=qtlnq/"
            self.send_data(self.auth_socket, qtlnq_data)

            # Send `type@=keylive` request.
            keeplive_data = self.prepare_keeplive_data()
            self.send_data(self.auth_socket, keeplive_data)

    def parse_regex(self, regex, target):
        pattern = re.compile(regex)
        match = pattern.search(target)
        return match.groups() if match else None

    def send_data(self, socket, data):
        logging.debug("send data:{}".format(data))
        enveloped_data = self.enveloped_data(data)
        socket.sendall(enveloped_data)

    # def recv_data(self, socket, size=4000):
    #     msg = socket.recv(size)
    #     msg = msg[12:-1].decode("utf-8", "ignore")

    def prepare_keeplive_data(self):
        timestamp = int(time.time())
        data = "type@=keeplive/tick@={}/vbw@=0/k@=19beba41da8ac2b4c7895a66cab81e23/".format(timestamp)
        return data

    def enveloped_data(self, data):
        """4 bits mark data length, 4 bits mark code(as data length), 4bits
        mark magic, 1 bits mark end string
        """
        length_str = "{:0<10}".format(hex(len(data)+9))
        tmp_list = []
        for i in range(2, 10, 2):
            tmp_list.append(binascii.unhexlify(length_str[i:i+2]))

        length_bytes = bytearray(tmp_list)
        code_bytes = length_bytes
        magic_bytes = bytearray([0xb1, 0x02, 0x00, 0x00])
        end_bytes = bytearray([0x00])
        data_bytes = bytes(data.encode("utf-8"))

        return length_bytes+code_bytes+magic_bytes+data_bytes+end_bytes

    def start_danmu(self):
        # Send login request.
        login_data = "type@=loginreq/username@={}/password@=1234567890123456/roomid@={}/".format(self.username, self.room_id)
        self.send_data(self.danmu_socket, login_data)
        msg = self.danmu_socket.recv(4000)
        logging.debug("auth login msg:{}".format(msg))

        # Send join gropu request.
        group_data = "type@=joingroup/rid@={}/gid@={}/".format(self.room_id, self.gid)
        self.send_data(self.danmu_socket, group_data)

        # keeplive thread run
        thread = threading.Thread(target=self.keeplive)
        thread.setDaemon(True)
        thread.start()
        while True:
            msg = self.danmu_socket.recv(4000)
            logging.debug("danmu recv msg:{}".format(msg))
            if "type@=uenter" in msg:
                result = self.parse_regex("/nn@=(.*?)/level", msg)
                try:
                    logging.info("弹幕:{}进入直播间".format(result[0]))
                except:
                    pass

            elif "type@=chatmsg" in msg:
                result = self.parse_regex("nn@=(.*?)/txt@=(.*?)/cid", msg)
                try:
                    nickname = result[0]
                    txt = result[1]
                    logging.info("弹幕:{}:{}".format(nickname, txt))
                except:
                    pass
            else:
                if len(msg) == 0:
                    logging.info("lose connect from danmu server!")
                    break
                logging.info("弹幕:其他消息")

    def keeplive(self):
        logging.info("keep live thread start...")
        while True:
            data = self.prepare_keeplive_data()
            self.send_data(self.auth_socket, data)
            self.send_data(self.danmu_socket, data)
            time.sleep(30)

    def start(self):
        self.init_socket()
        self.connect_server()
        if self.live_stat:
            self.start_danmu()
