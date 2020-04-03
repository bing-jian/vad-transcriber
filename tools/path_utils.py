# -*- coding: UTF-8 -*-

import os


def parse_filename(filename):
    abs_filename = os.path.abspath(filename)
    full_basename = os.path.splitext(abs_filename)[0]
    ext_name = os.path.splitext(abs_filename)[1]
    dir_name = os.path.dirname(full_basename)
    leaf_basename = os.path.basename(full_basename)
    return dir_name, leaf_basename, ext_name


def create_dir(dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)


def toplevel_subdirs(dirname):
    return [name for name in os.listdir(dirname) if os.path.isdir(os.path.join(dirname, name))]


def create_filename_pattern(input_pattern, ext):
    if os.path.isdir(input_pattern):
        input_pattern = os.path.join(input_pattern, '*.' + ext)
    return input_pattern


def extract_prefix(basename, prefix_len):
    if prefix_len <= 0:
        return basename
    return basename[:prefix_len]
