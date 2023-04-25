from pmk import PMK
from pmk.platform.keybow2040 import Keybow2040
import usb_cdc

keybow = PMK(Keybow2040())

# Attach handler functions to all of the keys
for key in keybow.keys:
    # A press handler that sends the keycode and turns on the LED
    @keybow.on_press(key)
    def press_handler(key):
        usb_cdc.data.write(bytes([key.number, 1]))

    # A release handler that turns off the LED
    @keybow.on_release(key)
    def release_handler(key):
        usb_cdc.data.write(bytes([key.number, 0]))

usb_cdc.data.reset_input_buffer()

while True:
    # Always remember to call keybow.update()!
    keybow.update()

    if usb_cdc.data.in_waiting >= 4:
        data = usb_cdc.data.read(4)
        index, r, g, b = data
        keybow.set_led(index, r, g, b)
