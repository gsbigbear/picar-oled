# menu-oled

Gestion du menu oled


    wget -O - https://raw.githubusercontent.com/gsbigbear/picar-oled/main/install.sh | bash


LCD-35

    git clone https://github.com/goodtft/LCD-show.git
    chmod -R 755 LCD-show
    cd LCD-show/
    sudo ./LCD35-show

kiosk

    sudo apt-get install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox
    sudo apt-get install --no-install-recommends chromium-browser
    sudo nano /etc/xdg/openbox/autostart
    
    xset -dpms            # turn off display power management system
    xset s noblank        # turn off screen blanking
    xset s off            # turn off screen saver
    # Remove exit errors from the config files that could trigger a warning

    sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/'Local State'

    sed -i 's/"exited_cleanly":false/"exited_cleanly":true/; s/"exit_type":"[^"]\+"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences
    
    # Run Chromium in kiosk mode
    chromium-browser  --noerrdialogs --disable-infobars --kiosk $KIOSK_URL
    
    sudo nano ~/.bash_profile
    
    [[ -z $DISPLAY && $XDG_VTNR -eq 1 ]] && startx -- -nocursor
    
    
    
