#!/usr/bin/python3
import argparse
import queue
import socket as sock
import struct
import threading
import time

TIME_1970 = 2_208_988_800


class SNTPServer:
    _sntp_unpacker = struct.Struct("!3Bb36xII")
    _sntp_reply_packer = struct.Struct("!3Bb20x6I")

    def __init__(self, port=123, delay=0, logger=print, thread_count=2):
        super().__init__()
        self.socket = None
        self._is_socket_ok = threading.Event()
        self._is_socket_ok.clear()
        self._task_queue = queue.Queue()
        self.port = port
        self.delay = delay
        self.logger = logger
        self.thr_count = thread_count

    def get_time(self):
        t = time.time() + self.delay
        seconds = int(t)
        fraction = int((t - seconds) * (2 ** 32))
        return seconds + TIME_1970, fraction

    # 0011 1000 = 0x38
    # 1100 0000 = 0xc0
    def get_sntp_reply(self, request: bytes, rc_second, rc_fraction):
        li = 0x00
        stratum = 1
        r_first_byte, r_stratum, poll, precision, \
        tr_second, tr_fraction = SNTPServer._sntp_unpacker.unpack(request[:48])
        vn = r_first_byte & 0x38
        mode = r_first_byte & 0x07
        if mode != 3:
            raise ValueError("not mode")
        first_byte = li + vn + 4
        return SNTPServer._sntp_reply_packer.pack(first_byte, stratum, poll, -10,
                                                  tr_second, tr_fraction,
                                                  rc_second, rc_fraction,
                                                  *self.get_time())

    def response(self):
        try:
            thr_id = threading.currentThread().getName()
            while self._is_socket_ok.is_set():
                try:
                    data, addr, r_time = self._task_queue.get(block=True, timeout=0.1)
                    self.logger("Request from:", addr, "Worked by:", thr_id)
                    time.sleep(0.5)
                    reply = self.get_sntp_reply(data, *r_time)
                    self.socket.sendto(reply, addr)
                except queue.Empty:
                    pass
        except sock.error as err:
            self.logger(err.args)
            self._is_socket_ok.clear()

    def run_server(self):
        try:
            self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
            self._is_socket_ok.set()
            for _ in range(self.thr_count):
                threading.Thread(target=self.response).start()
            self.socket.bind(('', self.port))
            self.logger("Server run!")
            while self._is_socket_ok.is_set():
                data, addr = self.socket.recvfrom(2048)
                self._task_queue.put((data, addr, self.get_time()))
                # self.response()
        except sock.error as err:
            self.logger(err.args)
        finally:
            self._is_socket_ok.clear()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=123,
                        help="port for listening")
    parser.add_argument('-d', '--delay', type=int, default=0,
                        help="the number of seconds for which"
                             " clients should be deceived")
    parser.add_argument('-t', '--threads', type=int, default=1,
                        help='count of thread for work in program')
    args = parser.parse_args()
    server = SNTPServer(args.port, args.delay, thread_count=args.threads)
    try:
        server.run_server()
    except PermissionError:
        print("Not enough privilege")


if __name__ == '__main__':
    main()
