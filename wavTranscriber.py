import glob
import webrtcvad
import logging
import wavSplit
from deepspeech import Model
from timeit import default_timer as timer

'''
Load the pre-trained model into the memory
@param models: Output Grapgh Protocol Buffer file
@param lm: Language model file
@param trie: Trie file

@Retval
Returns a list [DeepSpeech Object, Model Load Time, LM Load Time]
'''
def load_model(models, lm, trie):
    BEAM_WIDTH = 500
    LM_ALPHA = 0.75
    LM_BETA = 1.85

    model_load_start = timer()
    ds = Model(models, BEAM_WIDTH)
    model_load_end = timer() - model_load_start
    logging.debug("Loaded model in %0.3fs." % (model_load_end))

    lm_load_start = timer()
    ds.enableDecoderWithLM(lm, trie, LM_ALPHA, LM_BETA)
    lm_load_end = timer() - lm_load_start
    logging.debug('Loaded language model in %0.3fs.' % (lm_load_end))

    sample_rate = ds.sampleRate()
    logging.debug('Loaded model sample rate: %dHz.' % (sample_rate))

    return [ds, model_load_end, lm_load_end, sample_rate]

'''
Run Inference on input audio file
@param ds: Deepspeech object
@param audio: Input audio for running inference on
@param fs: Sample rate of the input audio file

@Retval:
Returns a list [Inference, Inference Time, Audio Length]

'''
def stt(ds, audio, fs):
    inference_time = 0.0
    audio_length = len(audio) * (1 / fs)

    # Run Deepspeech
    logging.debug('Running inference...')
    inference_start = timer()
    output = ds.stt(audio)
    inference_end = timer() - inference_start
    inference_time += inference_end
    logging.debug('Inference took %0.3fs for %0.3fs audio file.' % (inference_end, audio_length))

    return [output, inference_time]

'''
Resolve directory path for the models and fetch each of them.
@param dirName: Path to the directory containing pre-trained models

@Retval:
Retunns a tuple containing each of the model files (pb, lm and trie)
'''
def resolve_models(dirName):
    pb = glob.glob(dirName + "/*.pb")[0]
    logging.debug("Found Model: %s" % pb)

    lm = glob.glob(dirName + "/lm.binary")[0]
    trie = glob.glob(dirName + "/trie")[0]
    logging.debug("Found Language Model: %s" % lm)
    logging.debug("Found Trie: %s" % trie)

    return pb, lm, trie

'''
Generate VAD segments. Filters out non-voiced audio frames.
@param waveFile: Input wav file to run VAD on.0

@Retval:
Returns tuple of
    segments: a bytearray of multiple smaller audio frames
              (The longer audio split into mutiple smaller one's)
    sample_rate: Sample rate of the input audio file
    audio_length: Duraton of the input audio file

'''
def vad_segment_generator(wavFile, aggressiveness, model_sample_rate):
    logging.debug("Caught the wav file @: %s" % (wavFile))
    audio, sample_rate, audio_length = wavSplit.read_wave(wavFile)
    assert sample_rate == model_sample_rate, \
        "Audio sample rate must match sample rate of used model: {}Hz".format(model_sample_rate)
    vad = webrtcvad.Vad(int(aggressiveness))
    frames = wavSplit.frame_generator(30, audio, sample_rate)
    frames = list(frames)
    segments = wavSplit.vad_collector(sample_rate, 30, 300, vad, frames)

    return segments, sample_rate, audio_length
