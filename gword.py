#!/usr/bin/env python3
import sys, os
from gendict import get_word_def
from subprocess import getoutput, call, Popen

'''
play sound:
mpg123 'http://translate.googleapis.com/translate_tts?ie=UTF-8&client=gtx&tl=en&q=remedy'
mpg123 'http://translate.googleapis.com/translate_tts?ie=UTF-8&client=gtx&tl=zh-CN&q={encode(旋律)}'


'''

def is_sound_on():
    self = is_sound_on
    if not hasattr(self, "c"):
        if "✅" in os.getenv("PROMPT", ""):  # only check my own PROMPT
            output = getoutput("system_profiler SPAudioDataType")
            self.c = "Headphones" in output
        else:
            self.c = True
    return self.c

def play_word(word: str):
    if is_sound_on():
        # echo -n "hello" | espeak
        # echo -n "hello" | say
        Popen(["say", word])
    wd = get_word_def(word)
    if wd:
        print(f"\033[92m{wd.phonetic}\033[0m\n")
        print(wd.explanation)
    # else:
    #     print(f"{word}: no definition found")
    return wd
