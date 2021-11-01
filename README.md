# sensorstation

Raspberry Pi environment monitoring scripts

## Installation

    $ pipenv install --three

## Additional PMS7003 steps:

Enable serial: `raspi-config nonint set_config_var enable_uart 1 /boot/config.txt`
Disable serial terminal: `sudo raspi-config nonint do_serial 1`
Add `dtoverlay=pi3-miniuart-bt` to your /boot/config.txt
