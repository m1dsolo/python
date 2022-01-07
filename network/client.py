import socket
import select
import PySimpleGUI as sg

class Model:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.connect(("127.0.0.1",8888))

        self.epoll = select.epoll()
        self.epoll.register(self.socket.fileno(), select.EPOLLIN)
    
    def send(self, data):
        self.socket.sendall(data.encode())

    def recv(self):
        return self.socket.recv(1024).decode()

    def __del__(self):
        self.socket.close() 

    def run(self):
        events = self.epoll.poll(0)

        for fd, event in events:
            if event & select.EPOLLIN:
                data = self.recv()
                if data:
                    return (event, data)

        return (None, None)

class View:
    def __init__(self):
        sg.theme("GreenTan")

        layout = [[sg.Multiline(size=(110, 30), font=("Helvetica 10"), key="-OUTPUT-", write_only=True)], 
                [sg.Multiline(size=(60, 3), enter_submits=True, key="-INPUT-"), 
                sg.Button("SEND", button_color=(sg.YELLOWS[0], sg.BLUES[0]), bind_return_key=True), 
                sg.Button("EXIT", button_color=(sg.YELLOWS[0], sg.GREENS[0]))]]

        self.window = sg.Window("chat window", layout, font=("Helvetica", "13"), default_button_element_size=(8, 2))
        
    def show(self, *args, **kwargs):
        self.window["-OUTPUT-"].print(*args, **kwargs)
        
    def run(self):
        event, value = self.window.read(timeout=0)

        if event in ("SEND", "-INPUT-"):
            data = value["-INPUT-"].rstrip()
            self.window["-INPUT-"].update("")
            return (event, data)
        elif event in (None, "EXIT"):
            return ("EXIT", None)
        
        return (None, None)

    def __del__(self):
        self.window.close()

class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()

    def run(self):
        event, data = self.model.run()
        if event == select.EPOLLIN:
            self.view.show(data)

        event, data = self.view.run()
        if event == "SEND":
            self.model.send(data)
        elif event == "EXIT":
            return False

        return True

if __name__ == "__main__":
    controller = Controller()

    while True:
        if not controller.run():
            break

    del controller
