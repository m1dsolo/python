import socket
import select
import PySimpleGUI as sg


class Model:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("127.0.0.1", 8888))
        self.socket.listen(10)
        self.socket.setblocking(False)  

        self.epoll = select.epoll()
        self.epoll.register(self.socket.fileno(), select.EPOLLIN)
        self.fd_to_socket = {self.socket.fileno(): self.socket}

    def run(self):
        events = self.epoll.poll(0)

        for fd, event in events:
            socket = self.fd_to_socket[fd]

            if socket == self.socket:
                c, addr = socket.accept()
                c.setblocking(False)
                self.epoll.register(c.fileno(), select.EPOLLIN)
                self.fd_to_socket[c.fileno()] = c

                yield ("connection", addr)


            elif event & select.EPOLLHUP:
                addr, port = socket.getpeername()

                self.epoll.unregister(fd)
                self.fd_to_socket[fd].close()
                del self.fd_to_socket[fd]

                yield ("hangup", "{}:{}".format(addr, port))

            elif event & select.EPOLLIN:
                addr, port = socket.getpeername()
                data = socket.recv(1024).decode()

                if data:
                    for fd, c in self.fd_to_socket.items():
                        if c is not self.socket:
                            c.send("{}:{}:{}".format(addr, port, data).encode())
                    yield ("recv", "{}:{}:{}".format(addr, port, data))

    def __del__(self):
        self.epoll.unregister(self.socket.fileno())
        self.epoll.close()
        self.socket.close()


class View:
    def __init__(self):
        sg.theme("GreenTan")

        layout = [[sg.Multiline(size=(110, 30), font=("Helvetica 10"), key="-OUTPUT-")], 
                [sg.Button("EXIT", button_color=(sg.YELLOWS[0], sg.GREENS[0]))]]

        self.window = sg.Window("Chat server", layout, font=("Helvetica", "13"))

    def show(self, *args, **kwargs):
        self.window["-OUTPUT-"].print(*args, **kwargs)

    def run(self):
        event, value = self.window.read(timeout=0)

        if event in (sg.WIN_CLOSED, "EXIT"):
            return ("EXIT", None)

        return (None, None)

    def __del__(self):
        self.window.close()

class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()

    def run(self):
        for event, data in self.model.run():
            self.view.show("{}:{}".format(event, data))

        event, data = self.view.run()
        if event == "EXIT":
            return False

        return True

if __name__ == "__main__":
    controller = Controller()

    while True:
        if not controller.run():
            break


