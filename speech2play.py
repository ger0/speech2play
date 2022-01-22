#!/bin/python3
from subprocess import call
import glob
import difflib
import speech_recognition as sr
import serial
import vlc

AUDIO_EXTS = '*.mp3'
AUDIO_PATH = '/home/pi/Music/'

# list of audio files 
files = glob.glob(AUDIO_PATH + AUDIO_EXTS)

# microphone
r = sr.Recognizer()
m = sr.Microphone()

# arduino serial for LCD
ser = serial.Serial('/dev/ttyACM0', 9600, timeout = 1)
ser.reset_input_buffer()

# is a song playing?
isPlaying   = False
# is the program running?
isRunning   = True
shouldEcho  = False
nowPlaying  = ''
# Media player in this case VLC
player = vlc.MediaPlayer()

# find a cleaner way?
LCD_CLEAR   = "$INPUT:CLEAR"
LCD_PLAY    = "$INPUT:NOW_PLAYING"
LCD_SPEAK   = "$INPUT:SPEAK_NOW"

def printLCD(var, force = False):
    if (shouldEcho or force):
        ser.write((var + '\n').encode('ascii'))

def synthesize(string):
    call(["espeak", string])

def listen(short = False):
    with sr.Microphone() as source:
        printLCD(LCD_CLEAR)
        if (shouldEcho):
            synthesize("What would you want me to do?")
        r.adjust_for_ambient_noise(source)
        # mark it on display
        printLCD(LCD_SPEAK)

        if (short):
            audio = r.record(source, duration = 3)
        else:
            audio = r.record(source, duration = 6)

        printLCD(LCD_CLEAR)
        if (shouldEcho):
            synthesize("Got it")
        return audio

def recognize_voice(audio):
    try:
        text = r.recognize_google(audio)
        #print("you said: " + text)
        return text
    except sr.UnknownValueError:
        #print("Google Speech Recognition could not understand")
        return ''
    except sr.RequestError:
        #print("Could not request results from Google")
        return ''

def trimFilename(filename):
    temp = filename.rstrip(AUDIO_EXTS)
    temp = temp.lstrip(AUDIO_PATH)
    return temp

def matchKeywords(str_list):
    return difflib.get_close_matches(' '.join(str_list), files, 1, 0.1)

# returns True if parsed correctly
def parse(data):
    global isPlaying
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
                return True
            else:
                filename = filename[0]
                isPlaying = True
                synthesize("Playing a song")
                # save the name of a song
                nowPlaying = trimFilename(filename)
                # initiate vlc
                player = vlc.MediaPlayer(filename)
                player.play()
                return True
        # stop playing 
        elif (command[0] == 'stop' and isPlaying):
            isPlaying = False
            nowPlaying = ''
            player.stop()
            printLCD(LCD_CLEAR)
            return True
        elif (command[0] == 'nothing'):
            return True
        elif (command[0] == 'exit'):
            isRunning = False
            return True 
    # didn't recognize
    synthesize("Couldn't undrstand, please repeat")
    return False

printLCD(LCD_CLEAR, force=True)
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
                    if (isPlaying):
                        printLCD(LCD_PLAY)
                        printLCD(nowPlaying)
                    shouldEcho = False
                    break
