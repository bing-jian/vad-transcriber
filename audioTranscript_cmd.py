import sys
import os
import logging
import argparse
import numpy as np
import wavTranscriber

from timeit import default_timer as timer
# Debug helpers
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

#https://github.com/Uberi/speech_recognition
import speech_recognition

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
    args = parser.parse_args()
    if args.stream is True:
        print("Opening mic for streaming")
    elif args.audio is not None:
        logging.debug("Transcribing audio file @ %s" % args.audio)
    else:
        parser.print_help()
        parser.exit()

    asr = speech_recognition.Recognizer()

    if args.audio is not None:
        title_names = ['Filename', 'Duration(s)', 'Inference Time(s)']
        print("\n%-30s %-20s %-20s" % (title_names[0], title_names[1], title_names[2]))

        inference_time = 0.0

        # Run VAD on the input file
        waveFile = args.audio
        segments, sample_rate, audio_length = wavTranscriber.vad_segment_generator(waveFile, args.aggressive)
        f = open(waveFile.replace(".wav", ".txt"), 'w')
        logging.debug("Saving Transcript @: %s" % waveFile.replace(".wav",".txt"))

        for i, (segment, start, end) in enumerate(segments):
            # Run Google ASR on the chunk that just completed VAD
            logging.debug("Processing chunk %05d: [%d, %d)" % (i, start, end))
            audio = np.frombuffer(segment, dtype=np.int16)
            start = timer()
            audio_data = speech_recognition.AudioData(audio, sample_rate, 2)
            
            try:
                text = asr.recognize_google(audio_data, language=args.lang)
            except speech_recognition.UnknownValueError:
                text = "Unintelligible"
            run_time = timer() - start
            output = (text, run_time)
            inference_time += output[1]
            logging.debug("Transcript: %s" % output[0])

            f.write(output[0] + "\n")

        # Summary of the files processed
        f.close()

        # Extract filename from the full file path
        filename, ext = os.path.split(os.path.basename(waveFile))
        logging.debug("************************************************************************************************************")
        logging.debug("%-30s %-20s %-20s" % (title_names[0], title_names[1], title_names[2]))
        logging.debug("%-30s %-20.3f %-20.3f " % (filename + ext, audio_length, inference_time))
        logging.debug("************************************************************************************************************")
        print("%-30s %-20.3f %-20.3f " % (filename + ext, audio_length, inference_time))
    else:
        with speech_recognition.Microphone() as source:
            print('You can start speaking now. Press Control-C to stop recording.')
            try:
                while True:
                    audio = asr.listen(source)
                    try:
                        print("Google Speech Recognition thinks you said: " + asr.recognize_google(audio, language=args.lang))
                    except:
                        print("Speech unintelligible")
            except KeyboardInterrupt:
                sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
