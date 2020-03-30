from pathlib import Path
import argparse
import glob
import os

# https://pypi.org/project/xpinyin/
from xpinyin import Pinyin
import chinese_utils

def process_dir(dir):
    files = sorted(glob.glob(os.path.join(os.getcwd(), dir, '*.txt')))

    p = Pinyin()
    for f in files:
        print("Processing " + Path(f).name)

        lines = []
        with open(f) as t:
            for l in t.readlines():
                l_new = chinese_utils.normalize_chinese_line(l)
                lines.append(p.get_pinyin(l_new, ' ', tone_marks='numbers'))
        lab = f.replace("txt", "lab")
        print(lab)
        open(lab, 'w').write(''.join(lines))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Convert transcribed txt files into Chinese pinyin.')
    parser.add_argument('dir', help="Directory with .txt files")
    args = parser.parse_args()
    process_dir(args.dir)
