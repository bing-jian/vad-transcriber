# vad-transcriber

The Python script in this repo performs transcription on long wav files.
They take in a wav file of any duration, use the WebRTC Voice Activity Detector (VAD)
to split it into smaller chunks and finally save a consolidated transcript.


### 1. Command line tool

The command line tool processes a wav file of any duration and returns a trancript
which will the saved in the same directory as the input audio file.

The command line tool gives you control over the aggressiveness of the VAD.
Set the aggressiveness mode, to an integer between 0 and 3.
0 being the least aggressive about filtering out non-speech, 3 is the most aggressive.

You may also specify the target language that the ASR engine will use. The default 
language is American English.

```
$ python audioTranscript_cmd.py --aggressive 1 --audio path/to/audio.wav --lang zh-CN

```
