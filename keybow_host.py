import subprocess
import sys
import time

import serial
import adafruit_board_toolkit.circuitpython_serial

class Macro:
    def __init__(self, script, idle_color=(0, 0, 0), active_color=(0, 0, 0)):
        self.script = script
        self.idle_color = idle_color
        self.active_color = active_color

    #15: Macro(['/bin/sleep', '1'], idle_color=(238,130,238), active_color=(138,43,226)),
keymap = {
    15: Macro(['/bin/sleep', '1'], idle_color=(30,50,30), active_color=(238,130,238)),
}

# TODO: use select or something similar?
if __name__ == '__main__':

    popens = {}

    keybows = [ comport for comport in adafruit_board_toolkit.circuitpython_serial.data_comports()
                        if 'Keybow 2040' == comport.product ]
    if len(keybows) == 0:
        print("Could not connect to Keybow: No Keybow data ports detected.", file=sys.stderr)
        sys.exit(1)
    if len(keybows) > 1:
        # TODO: let the user use the serial number to specify which port to listen on
        print("Could not connect to Keybow: More than one data port detected.", file=sys.stderr)
        sys.exit(1)

    keybow_device = keybows[0].device
    # TODO: should this be exclusive?
    # TODO: flow control? https://www.ibm.com/docs/en/aix/7.1?topic=communication-flow-control
    with serial.Serial(keybow_device) as data_port:
        time.sleep(1)
        for key in range(16):
            if key in keymap:
                data_port.write(bytes([key, *keymap[key].idle_color]))
            else:
                data_port.write(bytes([key, 0, 0, 0]))
        
        data_port.reset_input_buffer()

        try:
            while True:
                # check keys
                if data_port.in_waiting >= 2:
                    key, state = data_port.read(2)
                    if state == 1:
                        if key in keymap:
                            popens[key] = subprocess.Popen(keymap[key].script)
                            data_port.write(bytes([key, *keymap[key].active_color]))

                # check completed processes
                for key, popen in list(popens.items()):
                    if popen.poll() is not None:
                        data_port.write(bytes([key, *keymap[key].idle_color]))
                        del popens[key]
        except KeyboardInterrupt:
            data_port.reset_output_buffer()
            for key in keymap:
                n = data_port.write(bytes([key, 0, 0, 0]))

                # for some reason, even after the bytes have been written, the keybow on the other
                # end can't read them unless we're still open when the read happens; and we don't
                # get any feedback about that as far as I can tell
                time.sleep(.1)
