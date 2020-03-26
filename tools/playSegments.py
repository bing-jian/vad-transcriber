import pyaudio
import wave
import glob
import os
import argparse
import re
from pathlib import Path

# https://stackoverflow.com/a/4623518
def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [tryint(c) for c in re.split('([0-9]+)', s)]


def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)


parser = argparse.ArgumentParser(description='Play transcribed wav files along with transcript')
parser.add_argument('dir', help="Directory with .wav files")
args = parser.parse_args()
files = glob.glob(os.path.join(os.getcwd(), args.dir, '*.wav'))
sort_nicely(files)

# https://stackoverflow.com/a/17657304
chunk = 1024
for f in files:
    print("Playing " + Path(f).name)
    txt = f.replace("wav", "txt")
    with open(txt) as t:
        print(t.readlines())

    wav = wave.open(f, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format = p.get_format_from_width(wav.getsampwidth()), channels=wav.getnchannels(), rate=wav.getframerate(), output=True)
    data = wav.readframes(chunk)
    while len(data)>0:
        stream.write(data)
        data = wav.readframes(chunk)
    stream.stop_stream()
    stream.close()
    p.terminate()
