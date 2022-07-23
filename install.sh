cd ~
git clone https://github.com/gsbigbear/picar-oled.git
cd picar-oled
sudo cp oled.service /lib/systemd/system/
pip3 install Adafruit_SSD1306 Adafruit_BBIO
sudo systemctl daemon-reload
sudo systemctl start oled.service
sudo systemctl enable oled.service
