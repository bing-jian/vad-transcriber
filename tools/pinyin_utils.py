#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

pinyin_phoneme = re.compile('^[a-z]+[1-5]$')
english_phoneme = re.compile('^[A-Z0-2\.]+$')


def remove_tone(pinyin_line):
    ss = pinyin_line.split()
    ss_new = []
    unexpected = []
    for s in ss:
        if pinyin_phoneme.match(s):
            ss_new.append(s[:-1])  # remove tone
        elif english_phoneme.match(s):
            ss_new.append(s)  # keep english
        else:
            unexpected.append(s)
    return ' '.join(ss_new), unexpected
