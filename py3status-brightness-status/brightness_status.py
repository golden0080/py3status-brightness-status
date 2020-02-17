# -*- coding: utf-8 -*-


class Py3status:
    """
    The Py3status module that uses `brightnessctl` tool to control brightness of monitors etc.

    Color Options:
    - color_dark
    - color_bright
    """

    # Botton configurations
    # Scroll up
    button_up = 4
    # Scroll down
    button_down = 5
    # Right click
    button_min = 3
    button_max = None

    cache_timeout = 300
    format = "💡: {brightness_percentage}"

    # brightnessctl configurations
    # The device class to control, default to control "backlight" class
    ctl_class = "backlight"
    # The device to be controlled, default to all devices.
    ctl_device = "*"

    # Control configurations
    # The percentage changed for every up/down adjustment
    percentage_delta = 5
    dark_threshold = 50
    min_brightness = 20
    below_min_brightness = False

    def kill(self):
        # TODO: store the brightness status in py3status
        pass

    def post_config_hook(self):
        self.color_dark = self.py3.COLOR_DARK or "#00FFFF"
        self.color_bright = self.py3.COLOR_BRIGHT or "#FFFF00"

    def brightness_status(self):
        cached_until = self.py3.time_in(self.cache_timeout)
        command = self.py3.check_commands("brightnessctl")
        if not command:
            return {
                "full_text": "'brightnessctl' command not installed.",
                "color": self.py3.COLOR_DEGRADED,
                "cached_until": cached_until,
            }

        data, color = self._get_brightness_format_data()
        text_output = self.py3.safe_format(self.format, data)
        return {
            "full_text": text_output,
            "color": color,
            "cached_until": cached_until,
        }

    def _brightnessctl_base_command(self):
        return "brightnessctl -c {cls} -d \"{device}\" -m".format(
            cls=self.ctl_class, device=self.ctl_device)

    def _get_brightness_format_data(self):
        color = self.color_dark
        command_str = self._brightnessctl_base_command()
        brightness = brightness_percentage = ""
        try:
            output = self.py3.command_output(command_str)
            parts = output.strip().rsplit(",", 3)
            if len(parts) < 4:
                raise self.py3.CommandError(
                    msg="cannot parse brightnessctl output.",
                    error_code=2,
                    output="brightnessctl command output is invalid: %s" %
                    output,
                    error="brightnessctl output invalid.")
            brightness = parts[-3]
            brightness_percentage = parts[-2]
            percentage_int = int(brightness_percentage[:-1])
            if not self.below_min_brightness and (percentage_int <
                                                  self.min_brightness):

                brightness_percentage = self._percentage_format(
                    self.min_brightness)
                self._brightness_absolute_adjustment(brightness_percentage)

            percentage_int = int(brightness_percentage[:-1])
            if percentage_int > self.dark_threshold:
                color = self.color_bright

        except self.py3.CommandError as e:
            if e.error_code == 1:
                brightness = brightness_percentage = "N/A"
            else:
                raise

        return {
            "brightness": brightness,
            "brightness_percentage": brightness_percentage,
        }, color

    def _brightness_delta_adjustment(self, value, increase=False):
        command_str = "{base_command} s {value}{sign}".format(
            base_command=self._brightnessctl_base_command(),
            sign="+" if increase else "-",
            value=str(value))

        self.py3.command_run(command_str)

    def _brightness_absolute_adjustment(self, value):
        command_str = "{base_command} s {value}".format(
            base_command=self._brightnessctl_base_command(), value=str(value))

        self.py3.command_run(command_str)

    def _percentage_format(self, percentage):
        if isinstance(percentage, str) and percentage[-1] == "%":
            return percentage

        return "{min}%".format(min=str(percentage))

    def on_click(self, event):
        button = event["button"]
        if button in [self.button_up, self.button_down]:
            self._brightness_delta_adjustment(
                "%s%%" % str(self.percentage_delta),
                increase=(button == self.button_up))
        elif button == self.button_min:
            self._brightness_absolute_adjustment(
                self._percentage_format(self.min_brightness))
        elif button == self.button_max:
            self._brightness_absolute_adjustment("100%")


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
