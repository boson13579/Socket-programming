import wx
import socket
import threading
import select


class ChatServerGUI(wx.Frame):
    def __init__(self, parent, title):
        super(ChatServerGUI, self).__init__(parent, title=title, size=(400, 300))

        self.panel = wx.Panel(self)
        self.text_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.panel.SetSizer(self.sizer)

        self.server = ChatServer(self)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def log_message(self, message):
        wx.CallAfter(self.update_text_ctrl, message)

    def update_text_ctrl(self, message):
        self.text_ctrl.AppendText(message + "\n")

    def on_close(self, event):
        self.server.stop_server()
        wx.GetApp().ExitMainLoop()
        event.Skip()


class ChatServer:
    def __init__(self, gui):
        self.clients = []
        self.gui = gui

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(0)
        self.server.bind(("localhost", 12345))
        self.server.listen(5)

        self.inputs = [self.server]
        self.outputs = []
        self.closed = []
        self.message_queues = {}

        self.stop_event = threading.Event()
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.start()

    def run_server(self):
        self.gui.log_message("Server started. Waiting for connections.")
        while not self.stop_event.is_set():
            readable, writable, exceptional = select.select(
                self.inputs, self.outputs, self.closed
            )
            for s in readable:
                if s is self.server:
                    try:
                        client_socket, client_address = s.accept()
                        client_socket.setblocking(0)
                        self.inputs.append(client_socket)
                        self.outputs.append(client_socket)
                        self.message_queues[client_socket] = []
                        self.gui.log_message(
                            f"Connection established with {client_address}"
                        )
                    except:
                        pass
                else:
                    try:
                        data = s.recv(1024)
                        if data:
                            self.gui.log_message(
                                f'Received message from {s.getpeername()}: {data.decode("utf-8")}'
                            )
                            for i in self.outputs:
                                if i is not self.server:
                                    self.message_queues[i].append(data)
                        else:
                            self.gui.log_message(f"Connection closed with {s.getpeername()}")
                            self.inputs.remove(s)
                            self.outputs.remove(s)
                            s.close()
                            del self.message_queues[s]
                    except:
                        pass

            for s in writable:
                try:
                    next_msg = self.message_queues[s].pop(0)
                    try:
                        s.send(next_msg)
                    except:
                        self.closed.append(s)
                except:
                    pass

            for s in exceptional:
                try:
                    self.inputs.remove(s)
                    self.outputs.remove(s)
                    s.close()
                    del self.message_queues[s]
                    self.gui.log_message(f"Connection closed with {s.getpeername()}")
                except:
                    pass

    def stop_server(self):
        self.stop_event.set()
        self.server.close()


if __name__ == "__main__":
    app = wx.App(False)
    server_gui = ChatServerGUI(None, title="Chat Server")
    server_gui.Show()

    clients = []

    app.MainLoop()
