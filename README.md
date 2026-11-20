# RaspberryPi-WorkOut-QuickStart
A Kiosk UI that allows a TV to be used for mainly workout apps on the web without having to connect a full laptop.  This is mainly to launch sworkout app and allow mobile phone control locally

## Kill current running instance via SSH:
pkill -f launcher.py && python3 ~/RaspberryPi-WorkOut-QuickStart/launcher.py &

## Setting up the configs
Run the "Setup.sh" script as administrator which should setup all the raspberry pi configs needed in order to run this project. 
One the script is run reboot the pi to start the program. Note that rebooting will make it harder to modify things later.

## Returning to the menu page
Note: Currently this applies to Sworkit, JellyFin, and Spotify
Since the pages are opened as new pages pressing alt + f4 will close the current page. This happens on the browser level and it is possible to close the menu page as it is just a browser page

There is a home button on the "/remote" route that will take you back from the main tile page






# raspberry Pi Setup
# Boot Directly into the UI Without Showing the Desktop

On Raspberry Pi OS Trixie, labwc launches the taskbar (wf-panel-pi) and desktop wallpaper (pcmanfm --desktop) via /etc/xdg/labwc/autostart. You can hide those desktop elements and launch your quickstart UI cleanly at boot.
1. Enable Desktop Auto-Login & Disable Screen Blanking:
Run sudo raspi-config:
	• Go to System Options → Boot / Auto Login → Select Desktop Autologin.
	• Go to Display Options → Screen Blanking → Select No.
2. Configure labwc Autostart:
Create your user-level labwc configuration directory and autostart script:bash
mkdir -p ~/.config/labwc
nano ~/.config/labwc/autostart
Use code with caution.
Add the following lines to kill the desktop panel/wallpaper immediately upon login, start the Flask server, and open Chromium in full-screen kiosk mode:bash
# Hide the Raspberry Pi OS taskbar and desktop icons
pkill -f wf-panel-pi &
pkill -f pcmanfm &

# Start the Quickstart Python server
python3 /home/$USER/quickstart/launcher.py &

# Wait briefly for Flask to bind, then launch the tile menu in Kiosk mode
sleep 2
chromium --kiosk --noerrdialogs --disable-infobars --check-for-update-interval=31536000 http://localhost:5000 &
Use code with caution.
3. Add a Shortcut to Close Launched Apps (~/.config/labwc/rc.xml):
So users can easily close a launched web page and drop straight back to the Quickstart tiles using a keyboard or the phone remote, ensure Alt+F4 closes windows in labwc:bash
cp /etc/xdg/labwc/rc.xml ~/.config/labwc/rc.xml
Use code with caution.
(Standard rc.xml on Raspberry Pi OS already binds A-F4 to Close, so pressing Alt+F4—or adding an Alt+F4 button to remote.html—closes the launched webpage and reveals the Quickstart menu underneath.)
4. Reboot to Test:bash
sudo reboot
Use code with caution.
Would you like me to add a dedicated "Close App / Home" button to the mobile remote page (remote.html) so you can exit full-screen web pages back to the tile menu directly from your phone?
