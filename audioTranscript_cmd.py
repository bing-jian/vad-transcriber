import logging, os, sys
import multiprocessing.dummy

from datetime import timedelta
from multiprocessing import Process
from pathlib import Path
from threading import Lock

import moviepy.editor as mp
import numpy as np

#https://github.com/Uberi/speech_recognition
import speech_recognition
import srt

import wavTranscriber

# Debug helpers
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class AudioVideoSplitter:

    def __init__(self, aggressive, lang, output, threads):
        # Initialize arguments
        self.aggressive = aggressive
        self.lang = lang
        self.output = output
        os.makedirs(output, exist_ok=True)
        self.input_is_video = False

        self.asr = speech_recognition.Recognizer()
        self.transcript_list = []
        self.threads = threads
        self.mutex = Lock()

    def process_input(self, input_path):
        self.input_path = input_path
        if (Path(input_path).suffix == '.wav'):
            audio_path = input_path
        else:
            # Assume input is a video
            self.sound_data = mp.AudioFileClip(input_path)
            audio_path = Path(input_path).with_suffix('.wav').as_posix()
            try:
                # Combine channels and set sample rate
                self.sound_data.write_audiofile(
                    audio_path,
                    ffmpeg_params=['-ac', '1', '-ar', '16000'],
                    verbose=False,
                    logger=None)
                self.input_is_video = True
            except IndexError:
                logging.error("No audio found in file " + input_path)
                return
        self.transcript_list = []
        self.recognize(audio_path)
        srt_data = srt.compose(self.transcript_list)
        with open(Path(audio_path).with_suffix('.srt'), 'w') as f:
            f.write(srt_data)

    def write_vid(self, input_path, interval, out_path):
        vid_data = mp.VideoFileClip(input_path)
        subclip = vid_data.subclip(*interval)
        subclip.write_videofile(out_path + ".mp4", verbose=False, logger=None)

    def write_segment(self, segment_name, audio_data, interval, text):
        path = os.path.join(os.getcwd(), self.output, segment_name)

        # Audio clip
        wav_data = audio_data.get_wav_data()
        with open(path + '.wav', 'wb') as f:
            f.write(wav_data)

        # Transcript
        with open(path + '.txt', 'w') as f:
            f.write(text)

        if self.input_is_video:
            # Video clip
            p = Process(target=self.write_vid,
                        args=(self.input_path, interval, path))
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
            self.transcript_list.append(
                srt.Subtitle(index=len(self.transcript_list) + 1,
                             start=timedelta(seconds=start),
                             end=timedelta(seconds=end),
                             content=text))
            self.mutex.release()
        except speech_recognition.UnknownValueError:
            logging.debug("Segment %s unintelligible" % segment_name)

    def worker(self, args):
        # Called by thread pool
        self.process_segment(self.sample_rate, *args)

    def recognize(self, waveFile):
        segments, sample_rate, _ = wavTranscriber.vad_segment_generator(
            waveFile, self.aggressive)
        self.sample_rate = sample_rate

        p = multiprocessing.dummy.Pool(self.threads)
        p.map(self.worker, segments)


def main(args):
    if args.stream is True:
        print("Opening mic for streaming")
    elif args.audio is not None:
        logging.debug("Transcribing audio file @ %s" % args.audio)
    else:
        parser.print_help()
        parser.exit()

    if args.audio is not None:
        vs = AudioVideoSplitter(args.aggressive, args.lang, args.out,
                                args.threads)
        vs.process_input(args.audio)


import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        'Transcribe long audio files using webRTC VAD or use the mic input')
    parser.add_argument(
        '--aggressive',
        default=1,
        type=int,
        choices=range(4),
        required=False,
        help=
        'Determines how aggressive filtering out non-speech is. (Integer between 0-3)'
    )
    parser.add_argument('--audio',
                        required=False,
                        help='Path to the input audio (WAV format) or video.')
    parser.add_argument('--stream',
                        required=False,
                        action='store_true',
                        help='To use microphone input')
    parser.add_argument('--lang',
                        default='en-US',
                        help='Language option for running ASR.')
    parser.add_argument('--out',
                        required=False,
                        help='Output directory',
                        default='tmp')
    parser.add_argument('--threads',
                        default=1,
                        type=int,
                        required=False,
                        help='Number of concurrent voice segments to process')
    args = parser.parse_args()
    main(args)
