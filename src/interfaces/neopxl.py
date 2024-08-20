import time
import sys
import logging
import math

if sys.argv and len(sys.argv) > 1 and sys.argv[1] == "--mock":
    import src.mock.neopixel as neopixel  # use for non-Raspi testing
else:
    import neopixel # use for Raspi

import math
from enum import Enum

from src.utils.types import Action

class IntensityWheelValues(Enum):
    ON = 250
    BRIGHT = 70
    MEDIUM = 25
    LOW13 = 13
    LOW12 = 12
    LOW11 = 11
    LOW10 = 10
    LOW9 = 9
    LOW8 = 8
    LOW7 = 7
    LOW6 = 6
    LOW5 = 5
    LOW4 = 4
    LOW3 = 3
    LOW = 2
    OFF = 1
    OFF2 = 0
    
class NeopixelInterface():
    def __init__(self, port: int, nb_pixels: int):
        self.port = port
        self.nb_pixels = nb_pixels
        # The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
        # For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
        self.neopixel_client: neopixel.NeoPixel = neopixel.NeoPixel(port, nb_pixels, brightness=1, auto_write=False, pixel_order=neopixel.GRB)
        self.int_values = [intensity.value * 0.05 for intensity in IntensityWheelValues] 
        self.len_int_values = len(self.int_values)
        self.max_pulse_value = 255
        self.min_pulse_value = 50
        self.current_cycle_step = 0
        self.cycle_length = 100
        self.amplitude = (self.max_pulse_value - self.min_pulse_value) / 2
        self.offset = (self.max_pulse_value + self.min_pulse_value) / 2
        self.current_intensity = int(self.amplitude * math.sin(2 * math.pi * self.current_cycle_step / self.cycle_length) + self.offset)
        self.action_methods = {
            Action.OFF: self._off,
            Action.RED: self._red,
            Action.ORANGE: self._orange,
            Action.GREEN: self._green,
            Action.WHITE: self._white,
            Action.RUNNING_LIGHT: self._running_lights
        }

    def _off(self, pixels):
        for pixel in pixels:
            self.neopixel_client[pixel] = (50, 0, 0)

    def _red(self, pixels):
        for pixel in pixels:
            self.neopixel_client[pixel] = (255, 0, 0)

    def _orange(self, pixels):
        for pixel in pixels:
            self.neopixel_client[pixel] = (100, 255, 0)

    def _green(self, pixels):
        for pixel in pixels:
            self.neopixel_client[pixel] = (0, 255, 0)

    def _white(self, pixels):
        for pixel in pixels:
            self.neopixel_client[pixel] = (255, 255, 255)

    def _running_lights(self, pixels):
        base_color = (255, 255, 255)  # white
        c_time = time.time()
        tail_length = 4  # Length of the tail (including the brightest pixel)

        # Calculate the current "head" position on the ring
        head_position = int(c_time * 7) % len(pixels)

        # Brightness levels for each position in the tail
        brightness_levels = [1.0, 0.5, 0.25, 0.1]  # Explicit brightness values for the tail

        # Iterate over all pixels
        for i in range(len(pixels)):
            # Calculate the distance of the current pixel from the head position
            distance = (i - head_position) % len(pixels)
        
            if distance < tail_length:
                # Get the corresponding brightness level from the list
                intensity_factor = brightness_levels[distance]
                # Adjust color based on intensity
                adjusted_color = tuple(int(value * intensity_factor) for value in base_color)
                self.neopixel_client[pixels[i]] = adjusted_color
            else:
                # Turn off the pixel if it's not in the tail
                self.neopixel_client[pixels[i]] = (0, 0, 0)

    def update_pixels(self, pixels: list[int], action: Action):
        logging.debug(f"Updating pixels {pixels} with action: {action}")
        """ Update pixels given action, but only if we're not in MOCK mode """
        if not (sys.argv and len(sys.argv) > 1 and sys.argv[1] == "--mock"):
            method = self.action_methods.get(action)
            if method: #
                method(pixels)
            else:
                raise(f"ERROR: Unknown action: {action}. Please implement first!")
        else:
            logging.debug("Mock mode, not updating pixels.")

    def show_changes(self):
        logging.debug("Neopixel: Showing changes.")
        """ Move changes to the actual hardware """
        self.neopixel_client.show()
        self.current_cycle_step = self.current_cycle_step + 1
        if self.current_cycle_step == self.cycle_length - 1:
            self.current_cycle_step = 0
        self.current_intensity = int(self.amplitude * math.sin(2 * math.pi * self.current_cycle_step / self.cycle_length) + self.offset)

    def cleanup(self):
        """ Celan up """
        self.neopixel_client.deinit()
