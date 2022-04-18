sudo cp oled.service /lib/systemd/system/
pip install Adafruit_SSD1306 Adafruit_BBIO
sudo systemctl start oled.service
sudo systemctl enable oled.service
