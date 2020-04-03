#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import string

import cn_tn


def normalize_chinese_line(text):
    text = cn_tn.NSWNormalizer(text).normalize()

    # Punctuations removal
    old_chars = cn_tn.CHINESE_PUNC_LIST + string.punctuation  # includes all CN and EN punctuations
    new_chars = ' ' * len(old_chars)
    del_chars = ''
    text = text.translate(str.maketrans(old_chars, new_chars, del_chars))
    return text
