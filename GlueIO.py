#!/usr/bin/env python
# encoding: utf-8

import sys

#------------------------------------------------------------------------------
# [ FileReader class ] - read local files
#------------------------------------------------------------------------------
class FileReader:
    def __init__(self, filepath):
        self.filepath = filepath

    def read_utf8(self):
        try:
            import codecs
            f = codecs.open(self.filepath, encoding='utf_8', mode='r')
        except IOError as ioe:
            sys.stderr.write("Glue Plugin Error: Unable to open file for read with read_utf8() method.")
            raise ioe
        try:
            return f.read()
        except Exception as e:
            sys.stderr.write("Glue Plugin Error: Unable to read the file with UTF-8 encoding using the read_utf8() method.")
            raise e
        finally:
            f.close()

#------------------------------------------------------------------------------
# [ FileWriter class ] - write to local files
#------------------------------------------------------------------------------
class FileWriter:
    def __init__(self, filepath):
        self.filepath = filepath

    def write_utf8(self, text):
        try:
            import codecs
            f = codecs.open(self.filepath, encoding='utf_8', mode='w')
        except IOError as ioe:
            sys.stderr.write("Glue Plugin Error: Unable to open file for write with the write_utf8() method.")
            raise ioe
        try:
            f.write(text)
        except Exception as e:
            sys.stderr.write("Glue Plugin Error: Unable to write UTF-8 encoded text to file with the write_utf8() method.")
            raise e
        finally:
            f.close()
