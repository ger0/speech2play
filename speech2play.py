#!/bin/python3
from subprocess import call
import glob
import difflib
import speech_recognition as sr
import serial
import time
import vlc
import sys
import logging

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('tmp.log')
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S'
)
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)

AUDIO_EXTS = '.mp3'
AUDIO_PATH = '/home/pi/Music/'

# list of audio files 
files = glob.glob(AUDIO_PATH + '*' + AUDIO_EXTS)

# arduino serial for LCD
ser = serial.Serial('/dev/ttyACM0', 9600)
ser.reset_input_buffer()
ser.reset_output_buffer()

# microphone
r = sr.Recognizer()
m = sr.Microphone()

# is the program running?
isRunning   = True
shouldEcho  = True 
nowPlaying  = ''
# Media player in this case VLC
player  = vlc.MediaPlayer()

# find a cleaner way?
LCD_CLEAR   = "$INPUT:CLEAR"
LCD_PLAY    = "$INPUT:NOW_PLAYING"
LCD_SPEAK   = "$INPUT:SPEAK_NOW"

CYCLE_THRESHOLD = 5
responseCycles = 10

def printLCD(var):
    if (shouldEcho):
        ser.write((var + '\n').encode('ascii'))

def synthesize(string):
    call(["espeak", string])

def listen(short = False):
    global responseCycles
    with sr.Microphone() as source:
        printLCD(LCD_CLEAR)
        if (shouldEcho):
            synthesize("What would you want me to do?")
        # adusting for noise
        if (not short or responseCycles > CYCLE_THRESHOLD):
            print("Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(source)
            responseCycles = 0;
        # mark it on display
        printLCD(LCD_SPEAK)

        print("Listening now...")
        if (short):
            audio = r.record(source, duration = 3)
            #audio = r.listen(source)
            responseCycles += 1
        else:
            audio = r.listen(source)

        printLCD(LCD_CLEAR)
        if (shouldEcho):
            synthesize("Got it")
        return audio

def recognize_voice(audio):
    try:
        text = r.recognize_google(audio)
        logger.info("you said: " + text)
        return text
    except sr.UnknownValueError:
        #logger.info("Google Speech Recognition could not understand")
        return ''
    except sr.RequestError:
        logger.warning("Could not request results from Google")
        return ''

def trimFilename(filename):
    temp = filename.split(AUDIO_EXTS)[0]
    temp = temp.lstrip(AUDIO_PATH)
    return temp

def matchKeywords(str_list):
    return difflib.get_close_matches(' '.join(str_list), files, 1, 0.2)

def printPlaying():
    if (player.is_playing() == 1):
        printLCD(LCD_PLAY)
        printLCD(nowPlaying)

# returns True if parsed correctly
def parse(data):
    global isRunning
    global nowPlaying
    global player
    # split into a list
    command = (data.lower()).split()
    # play something
    if (len(command) > 0):
        if (len(command) > 1 and command[0] == 'play'):
            # ignore the 'play' keyword and match the most similar audiofile
            filename = matchKeywords(command[1:])
            if (len(filename) == 0):
                synthesize("Couldn't match a song")
                logger.info("Couldn't match any song")
                return True
            else:
                filename = filename[0]
                synthesize("Playing a song")
                # save the name of a song
                nowPlaying = trimFilename(filename)
                # initiate vlc
                media = vlc.Media(filename)
                player.set_media(media)
                player.play()
                logger.info("Playing a song: " + nowPlaying)

                # force printLCD
                printLCD(LCD_PLAY)
                printLCD(nowPlaying)
                return True
        # stop playing 
        elif (command[0] == 'stop'):
            if (player.is_playing() == 1):
                player.stop()
                nowPlaying = '' 
                printLCD(LCD_CLEAR)
                logger.info("Stopping playback")
            return True
        elif (command[0] == 'nothing'):
            return True
        elif (command[0] == 'exit'):
            printLCD("exiting")
            player.stop()
            isRunning = False
            return True 
    # didn't recognize
    synthesize("Couldn't understand, please repeat")
    return False

# is this neccessary? 
time.sleep(5)
logger.info("initialising...")
printLCD(LCD_CLEAR)
shouldEcho = False
while isRunning:
    audio       = listen(short=True)
    voice_line  = recognize_voice(audio)
    if ('hello' in voice_line):
        shouldEcho = True
        # do.. while?
        while True:
            printLCD(LCD_CLEAR)
            audio   = listen()
            voice_line = recognize_voice(audio)
            if (voice_line != False):
                if (parse(voice_line)):
                    printPlaying()
                    shouldEcho = False
                    break
# poweroff
logger.info("Shutting down...")
call(['sudo', 'shutdown', '-h', 'now'])
