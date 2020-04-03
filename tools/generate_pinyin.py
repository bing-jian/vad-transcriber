from pathlib import Path
import glob

# https://github.com/Kyubyong/g2pC
from g2pc import G2pC

import chinese_utils
import path_utils
import pinyin_utils


def batch(files):
    g2p = G2pC()
    for f in files:
        print("Processing " + Path(f).name)
        lines = []
        with open(f) as t:
            for l in t.readlines():
                normalized_line = chinese_utils.normalize_chinese_line(l)
                pinyin_line = ' '.join([x[3] for x in g2p(normalized_line)])
                pinyin_line, _ = pinyin_utils.remove_tone(pinyin_line)
                lines.append(pinyin_line)
        lab = Path(f).with_suffix('.lab').as_posix()
        print(lab)
        open(lab, 'w').write(''.join(lines))


import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Convert transcribed txt files into Chinese pinyin.')
    parser.add_argument('glob', help='Glob pattern of .txt files')
    args = parser.parse_args()
    input_pattern = path_utils.create_filename_pattern(args.glob, 'txt')
    files = sorted(glob.glob(input_pattern))
    batch(files)
