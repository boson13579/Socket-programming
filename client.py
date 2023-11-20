import wx
import socket
import threading
import select

class ChatClient(wx.Frame):
    def __init__(self, parent, title):
        super(ChatClient, self).__init__(parent, title=title, size=(400, 300))

        self.panel = wx.Panel(self)
        self.text_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.input_text = wx.TextCtrl(self.panel, style=wx.TE_PROCESS_ENTER)
        self.send_button = wx.Button(self.panel, label="Send")

        self.send_button.Bind(wx.EVT_BUTTON, self.send_message)
        self.input_text.Bind(wx.EVT_TEXT_ENTER, self.send_message)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.sizer.Add(self.input_text, flag=wx.EXPAND | wx.ALL, border=5)
        self.sizer.Add(self.send_button, flag=wx.EXPAND | wx.ALL, border=5)

        self.panel.SetSizer(self.sizer)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("localhost", 12345))
        self.client_socket.setblocking(0)

        self.inputs = [self.client_socket]
        self.outputs = []
        self.stop_event = threading.Event()
        self.receive_messages_thread = threading.Thread(target=self.receive_messages)
        self.receive_messages_thread.start()

    def send_message(self, event):
        message = self.input_text.GetValue()
        self.input_text.Clear()
        self.client_socket.send(message.encode("utf-8"))

    def receive_messages(self):
        while not self.stop_event.is_set():    
            try:
                readable, _, _ = select.select(self.inputs, self.outputs, self.inputs)
                for s in readable:
                    data = s.recv(1024)
                    if data:
                        wx.CallAfter(self.update_text_ctrl, data.decode("utf-8"))
                    else:
                        self.client_socket.close()
                        wx.CallAfter(self.update_text_ctrl, "Connection closed.")
                        return
            except:
                pass

    def update_text_ctrl(self, message):
        self.text_ctrl.AppendText(message + "\n")
    
    def on_close(self, event):
        self.stop_event.set()
        self.client_socket.close()
        self.Destroy()

if __name__ == "__main__":
    app = wx.App()
    frame = ChatClient(None, "Chat Client")
    frame.Show()
    app.MainLoop()
    
    