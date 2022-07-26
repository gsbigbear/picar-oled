#!/usr/bin/python3.7
import RPi.GPIO as GPIO
import sys, json, os, subprocess, multiprocessing, socket
from time import sleep
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import traceback, zic
from threading import Thread
import glob, time, threading
from tornado.httpserver import HTTPServer
import asyncio

manager = multiprocessing.Manager()

dict_to_play={"smland":{"title":"/home/pi/picar/copilot/audio/smland.mp3","startpos":0,"timetoplay":.75,"volume":2}}

def play_audio(dictplay,loop):
    time.sleep(2.2)
    for i in range(loop):
        try :
            result = os.system("mplayer -ao alsa:device=hw=1.0 -af volume={volume}:1 {title} -ss {startpos} -endpos {timetoplay}  >/dev/null 2>&1".format(**dictplay))
        except:
            break
        time.sleep(.5)

def playsound(dictplay,loop=1):
    thread = threading.Thread(target=play_audio, args=(dictplay,loop,))
    thread.start()

# GPIO mode
GPIO.setmode(GPIO.BCM)
os.chdir(sys.path[0])
# oled
disp = Adafruit_SSD1306.SSD1306_128_32(rst=None)
disp.begin()
font = ImageFont.truetype("FreeSans.ttf", 14)
disp.clear()
disp.display()

# init du tmux dédié
os.system("tmux has-session -t  oled || tmux new -d -s oled")

#static config load
os.chdir(sys.path[0])
with open('./oled_config.json', 'r') as f: config = json.load(f)
GlobalMap = manager.dict()
GlobalMap['line_display']=''
GlobalMap['btn_ack']=True
GlobalMap['btn_action']=True
GlobalMap['ip']=socket.gethostbyname(socket.gethostname())
print(GlobalMap)
# dynamic config load drives - cars
cars_path = "/home/pi/picar"
for path in glob.glob(cars_path):
    profile = os.path.basename(os.path.dirname(path))
    drive_sub_menu=[]
    if path != '':
        drive_sub_menu.append({
                "label":"Drive : {}".format(os.path.basename(profile))+"\n{}",
                "status": "/bin/bash -c 'ps -ef | grep -v grep | grep \" manage.py \" > /dev/null 2>&1 && echo running, stop && exit 1 || echo idle, start && exit 0'",
                "return_code_0":"cd {} ; /home/pi/env/bin/python3.7 manage.py drive --js".format(cars_path),
                "return_code_1":"purge_tmux",
                "tmux":True,
            })
        # model testing
        for path in glob.glob("{}/models/*.tflite".format(cars_path,profile)):
            filename = os.path.basename(path)
            extra_args="--type tflite_linear" if 'tflite' in path else ""
            #if os.path.exists(path+ ".py"):
            #    extra_args += " --myconfig=models/{}".format(filename+ ".py")
            drive_sub_menu.append({
                "label":"Modl: {}".format(filename)+"\n{}",
                "status": "/bin/bash -c 'ps -ef | grep -v grep | grep \" manage.py \" > /dev/null 2>&1 && echo running, stop && exit 1 || echo idle, start && exit 0'",
                "return_code_0":"cd {} ; /home/pi/env/bin/python3.7 manage.py drive --model=models/{} {}".format(cars_path,filename,extra_args),
                "return_code_1":"purge_tmux",
                "tmux":True,
            })
    if drive_sub_menu: 
        drive_sub_menu.append({"label":"< Retour"})
        drive_sub_menu.append({
                    "label":"Refresh model\nlist",
                    "status": "exit 0",
                    "return_code_0":"/bin/bash -c 'sudo service oled restart'",
                    "tmux":False
                })
        config['menu'].append({"label":"+ User : {}\n{} configs".format(profile,len(drive_sub_menu)-1),"submenu":drive_sub_menu})
 
### hat Gestion des boutons 
def init_btn():
    for pin,pin_id in config['pin_btn'].items() : 
        GPIO.setup(pin_id, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin_id,GPIO.RISING,callback=eval(pin))
        pins_btn.append(pin_id)
        
# hat - function interupt
def btn_left(*args):return button_pushed(sys._getframe().f_code.co_name)
def btn_small(*args): return button_pushed(sys._getframe().f_code.co_name)
def btn_right(*args):return button_pushed(sys._getframe().f_code.co_name)
def button_pushed(pin_label):
    if GlobalMap['btn_ack'] == True : GlobalMap['btn_action'],GlobalMap['btn_ack'] = pin_label,False # asynchrone

### hat - init des leds
def init_led() :
    for pin,pin_ids in config['pin_led'].items() : 
        globals()[pin]=list(pin_ids)
        for pin_id in pin_ids :
            GPIO.setup(pin_id, GPIO.OUT) 
            led_switch([pin_id],True)
            pins_led.append(pin_id)
            sleep(.1)    
            led_switch([pin_id],False)

# hat Fonction pour jouer avec les leds
def led_switch(pin_ids,force=None,wait=0):
    if force == False: pin_ids.reverse()
    for pin_id in pin_ids :
        if force == None : # on reverse le status actuel
            if GPIO.input(pin_id): GPIO.output(pin_id, GPIO.LOW)
            else: GPIO.output(pin_id, GPIO.HIGH)
        elif force == True : GPIO.output(pin_id, GPIO.HIGH)  # force status
        else : GPIO.output(pin_id, GPIO.LOW) # force status
        sleep(wait)

# menu - message sur oled
def show_oled(message) :
    GlobalMap['line_display']=message
    disp.clear()
    disp.display()
    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), message ,  font=font, fill=255)
    disp.image(image)
    disp.display()

# hat - animation police
def police(loop=5,wait=.1,to_play=[]):
    for this in to_play * loop:
        led_switch(this,True, wait)
        led_switch(this,False, wait)

# menu - affichage oled
def refresh_menu(menu,menu_x,menu_y):
    if menu_y == None : 
        show_oled(menu[menu_x]['label'])
        return None
    current = menu[menu_x]['submenu'][menu_y]
    if 'status' in current :
        result_code,result_str=run_command(current['status'],False)
        show_oled(current['label'].format(result_str))
        return [ current["return_code_{}".format(result_code)], current['tmux'] ]
    show_oled(current['label'])
    return "main_menu"

# lancement des commandes
def run_command(command=None,tmux=False) :
    led_switch(white,True)
    if command == 'purge_tmux' : 
        command = "/usr/bin/tmux send-keys -t oled C-c;"
    elif tmux == True : 
        command = 'tmux send -t oled "{}" ENTER \;'.format(command)
    if 'tmux' in command : # init du tmux oled si absent
        os.system("tmux has-session -t oled || tmux new -d -s oled") 
    
    sp = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE,stdin=None, shell=True)
    out, err = sp.communicate()
    if tmux: 
        led_switch(red,True,2)
        led_switch(red,False)
    led_switch(white,False)
    return sp.returncode, out.decode("utf-8")

import tornado.web 

class MessageHandler(tornado.web.RequestHandler):
    def initialize(self, shared_dict):
        self.shared_dict = shared_dict

    def get(self):
        self.render("index.html", **self.shared_dict)

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        print(data)

class InfoHandler(tornado.web.RequestHandler):
    def initialize(self, shared_dict):
        self.shared_dict = shared_dict

    def get(self):
        self.write(dict(self.shared_dict))

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        if 'button' in data: button_pushed(data['button'])

async def runhttp():
    tornado_settings = {
        'static_path': 'templates',
        'template_path': 'templates',
        'debug': True
    }
    app = tornado.web.Application([(r"/jquery-3.6.0.min.js()",tornado.web.StaticFileHandler, {"path":'templates/jquery-3.6.0.min.js'}),
                                   (r"/info", InfoHandler,dict(shared_dict=GlobalMap)),
                                   (r"/", MessageHandler,dict(shared_dict=GlobalMap))
    ],**tornado_settings)
    app.listen(8888)
    await asyncio.Event().wait()

def run_tornado():
    asyncio.run(runhttp())

if __name__ == '__main__':
    threadwww = multiprocessing.Process(target=run_tornado, args=())
    threadwww.start()
    pins_led = []
    pins_btn = []
    menu_x, menu_y  = [ len(config['menu']) -1 , 0 ] # on se positionne dans le menu drive
    GlobalMap['btn_ack'] = True
    menu_loop_sleep = .2
    try :
        init_led()
        init_btn()
        zic.setup(config['buzzer_cfg']['pin'])
        Thread(target=zic.play, args=(zic.melody[:14], zic.tempo, 1.3, .8)).start()
        playsound(dict_to_play["smland"])
        waiting_action = refresh_menu(config['menu'],menu_x,menu_y)
        while True:
            if not GlobalMap['btn_ack'] :
                led_switch(blue)
                if menu_y == None : # cas menu racine
                    if GlobalMap['btn_action'] == "btn_small" : menu_y = 0
                    elif GlobalMap['btn_action'] == "btn_right" : menu_x = 0 if menu_x == len(config['menu']) - 1 else menu_x + 1
                    elif GlobalMap['btn_action'] == "btn_left": menu_x = menu_x - 1 if menu_x > 0 else len(config['menu']) - 1
                else : # cas submenu
                    if GlobalMap['btn_action'] == "btn_small" :
                        if waiting_action == 'main_menu': menu_y = None
                        else : run_command(waiting_action[0],waiting_action[1])
                    elif GlobalMap['btn_action'] == "btn_right" : menu_y = 0 if menu_y == len(config['menu'][menu_x]['submenu'])- 1 else menu_y + 1
                    elif GlobalMap['btn_action'] == "btn_left": menu_y = menu_y - 1 if menu_y > 0 else len(config['menu'][menu_x]['submenu']) - 1 
                waiting_action = refresh_menu(config['menu'],menu_x,menu_y)
                GlobalMap['btn_ack'] = True
                led_switch(blue)
            sleep(menu_loop_sleep)
    except Exception :
        traceback.print_exc()
        threadwww.terminate() 
        pass
    finally:
        GPIO.cleanup([pin for pin in pins_led + pins_led + [config['buzzer_cfg']['pin']]])
