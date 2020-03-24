import sys
import os
import logging
import argparse
import numpy as np
import wavTranscriber
import moviepy.editor as mp
import tempfile
from timeit import default_timer as timer
import multiprocessing.dummy
from multiprocessing import Process
# Debug helpers
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

#https://github.com/Uberi/speech_recognition
import speech_recognition
from threading import Lock
from datetime import timedelta
import srt
from pathlib import Path
class VideoSplitter:
    def __init__(self, aggressive, lang, output, threads):
        # Initialize arguments
        self.aggressive = aggressive
        self.lang = lang
        self.output = output
        self.threads = threads

        self.asr = speech_recognition.Recognizer()

        self.transcript_list = []
        self.mutex = Lock()
        os.makedirs(output, exist_ok=True)

    def process_video(self, vid_path):
        self.vid_path = vid_path
        self.sound_data = mp.AudioFileClip(vid_path)

        # Temp file for audio wav
        fd, path = tempfile.mkstemp(suffix=".wav")
        
        try:
            # Combine channels and set sample rate
            self.sound_data.write_audiofile(path, ffmpeg_params=['-ac', '1', '-ar', '16000'], verbose=False, logger=None)
        except IndexError:
            logging.error("No audio found in file " + vid_path)
            return

        self.transcript_list = []
        self.recognize(path)
        srt_data = srt.compose(self.transcript_list)
        with open(Path(vid_path).with_suffix('.srt'), 'w') as f:
            f.write(srt_data)
        os.remove(path)

    def write_vid(self, vid_path, interval, out_path):
        vid_data = mp.VideoFileClip(vid_path)
        subclip = vid_data.subclip(*interval)
        subclip.write_videofile(
            out_path + ".mp4", verbose=False, logger=None)

    def write_segment(self, segment_name, audio_data, interval, text):
        path = os.path.join(os.getcwd(), self.output, segment_name)

        # Audio clip
        wav_data = audio_data.get_wav_data()
        with open(path + '.wav', 'wb') as f:
            f.write(wav_data)

        # Transcript
        with open(path + '.txt', 'w') as f:
            f.write(text)
        
        # Video clip
        p = Process(target=self.write_vid, args=(self.vid_path, interval, path))
        p.start()
        p.join()

    def process_segment(self, rate, segment, start, end):
        segment_name = "%.3f_%.3f" % (start, end)
        audio = np.frombuffer(segment, dtype=np.int16)
        audio_data = speech_recognition.AudioData(audio, rate, 2)
        try:
            text = self.asr.recognize_google(audio_data, language=self.lang)
            logging.debug("Segment %s transcript: %s" % (segment_name, text))
            self.write_segment(segment_name, audio_data, (start, end), text)
            
            self.mutex.acquire()
            self.transcript_list.append(srt.Subtitle(index=len(self.transcript_list)+1, start=timedelta(seconds=start), end=timedelta(seconds=end), content=text))
            self.mutex.release()
        except speech_recognition.UnknownValueError:
            logging.debug("Segment %s unintelligible" % segment_name)

    def worker(self, args):
        # Called by thread pool
        self.process_segment(self.sample_rate, *args)

    def recognize(self, waveFile):

        segments, sample_rate, _ = wavTranscriber.vad_segment_generator(waveFile, self.aggressive)
        self.sample_rate = sample_rate
        
        p = multiprocessing.dummy.Pool(self.threads)
        p.map(self.worker, segments)

            

def main(args):
    parser = argparse.ArgumentParser(description='Transcribe long audio files using webRTC VAD or use the mic input')
    parser.add_argument('--aggressive', default=1, type=int, choices=range(4), required=False,
                        help='Determines how aggressive filtering out non-speech is. (Integer between 0-3)')
    parser.add_argument('--audio', required=False,
                        help='Path to the audio file to run (WAV format)')
    parser.add_argument('--stream', required=False, action='store_true',
                        help='To use microphone input')
    parser.add_argument('--lang', default='en-US',
                        help='Language option for running ASR.')
    parser.add_argument('--out', required=False, help='Output directory')
    parser.add_argument('--threads', default=1, type=int, required=False, help='Number of concurrent voice segments to process')
    args = parser.parse_args()
    if args.stream is True:
        print("Opening mic for streaming")
    elif args.audio is not None:
        logging.debug("Transcribing audio file @ %s" % args.audio)
    else:
        parser.print_help()
        parser.exit()

    if not args.out:
        args.out = "output"

    if args.audio is not None:
        vs = VideoSplitter(args.aggressive, args.lang, args.out, args.threads)
        vs.process_video(args.audio)


if __name__ == '__main__':
    main(sys.argv[1:])
