"""
GUI that exposes main parameters of serial relay program

MUST:
    Text entry boxes for hostname/ip (autodetect, errorcheck)
    Text entry box for smart agent name
    Text entry box for port (advanced users - default is 1883)
    Radio buttons for protocol (advanced users)
    Free text box for printed output/messages/errors
    

SHOULD
    Reset button
    Help menu
    Run on all operating systems (to which I have access)

COULD
    Display list of connected arduinos
    Display full network map (broker services)
    
"""

import tkinter
import serial_relay


global SPACING
global BACKGROUND
global FONT

class ScrollTextFrame():
    def __init__(self, parent, padding, labeltext, height):
        
        self.frame = tkinter.Frame(parent, borderwidth=1, bg=BACKGROUND,)
        self.frame.pack(side=tkinter.LEFT, padx=padding, pady=padding)

        self.label = tkinter.Label(self.frame, justify=tkinter.LEFT, padx=10,
                                   bg=BACKGROUND,
                                   font=(FONT, 12),
                                    text=labeltext).pack()
        self.scrollbar = tkinter.Scrollbar(self.frame)
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.textbox = tkinter.Text(self.frame, height=height, width=25)
        self.textbox.pack()
        
        # attach listbox to scrollbar
        self.textbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.textbox.yview)
    
class InputBox():
    '''
    Creates an input box with label
    '''
    def __init__(self, parent, labeltext, default=''):
        self.label = tkinter.Label(parent, justify=tkinter.LEFT,
                                   bg=BACKGROUND,
                                  font=(FONT, 12),
                                  text=labeltext).pack()
        self.inputbox = tkinter.Entry(parent, width=30)
        self.inputbox.insert(0, default)
        self.inputbox.pack()

def start_callback():
    '''
    Check input
    '''
    broker_name = cloud_name_choice.inputbox.get()
    if broker_name == '':
        status_frame.textbox.insert(tkinter.END, 'Please fill in a cloud name\n')
        status_frame.textbox.see(tkinter.END)
        return None
    smart_agent_name = user_name_choice.inputbox.get()
    if smart_agent_name == '':
        status_frame.textbox.insert(tkinter.END, 'Please fill in a user name\n')
        status_frame.textbox.see(tkinter.END)
        return None
    port = port_choice.inputbox.get()
    if port == '':
        status_frame.textbox.insert(tkinter.END, 'No port chosen: using default (1883)\n')
        port = 1883
    else:
        try:
            port = int(port)
        except:
            status_frame.textbox.insert(tkinter.END, 'Need an integer port: using default (1883)\n')
            port = 1883
            
    protocol = 
    status_frame.textbox.see(tkinter.END)
    
    
    
    print('START')
    
def stop_callback():
    print('STOP')
    
    
SPACING = 10
BACKGROUND = 'LightSteelBlue1'
FONT = 'Helvetica'

root = tkinter.Tk("Internet of thingies")
root.configure(bg=BACKGROUND)

title_frame = tkinter.Frame(root, borderwidth=1)
title_frame.configure(bg=BACKGROUND)
title_frame.pack(padx=SPACING, pady=SPACING)

title_label = tkinter.Label(title_frame, justify=tkinter.LEFT, padx=SPACING,
                            bg=BACKGROUND,
                            font=(FONT, 24),
                            text="Internet of Thingies").pack()



centre_frame = tkinter.Frame(root, borderwidth=1)
centre_frame.configure(bg=BACKGROUND)
centre_frame.pack(padx=SPACING, pady=SPACING)

'''
CONFIGURATION 
'''

left_centre_frame = tkinter.Frame(centre_frame, bg=BACKGROUND, borderwidth=1)



cloud_name_choice = InputBox(left_centre_frame, "Cloud network address")
user_name_choice = InputBox(left_centre_frame, "This computer's name")
port_choice = InputBox(left_centre_frame, "Cloud network port (advanced)", default='1883')

status_frame = ScrollTextFrame(left_centre_frame, SPACING, "Status", 12)
left_centre_frame.pack(side=tkinter.LEFT, padx=SPACING, pady=SPACING)

'''
OUTPUT DATA
'''
sent_messages_frame = ScrollTextFrame(centre_frame, SPACING, "Messages sent", 20)
received_messages_frame = ScrollTextFrame(centre_frame, SPACING, "Messages received", 20)

'''
NETWORK VIEW
'''
network_data_frame = ScrollTextFrame(centre_frame, SPACING, "Network", 20)


'''
CONTROL BUTTONS
'''
bottom_frame = tkinter.Frame(root, borderwidth=1)
bottom_frame.configure(bg=BACKGROUND)
bottom_frame.pack(padx=SPACING, pady=SPACING)

stop_button = tkinter.Button(bottom_frame, text="STOP", command=stop_callback)
stop_button.pack(side=tkinter.RIGHT, padx=SPACING, pady=SPACING)

# The start button kickstarts this whole thing
start_button = tkinter.Button(bottom_frame, text="START", command=start_callback)
start_button.pack(side=tkinter.RIGHT)


'''
When the start button is pressed:
    - The program checks if all the fields have been filled in.
    - In status: Input looks okay
    - In status: Attempting to connect to the broker
'''

root.mainloop()