#!/usr/bin/env python3
import sys, os
from gendict import get_word_def,is_sound_on
from subprocess import getoutput, call, Popen

'''
play sound:
mpg123 'http://translate.googleapis.com/translate_tts?ie=UTF-8&client=gtx&tl=en&q=remedy'
mpg123 'http://translate.googleapis.com/translate_tts?ie=UTF-8&client=gtx&tl=zh-CN&q={encode(旋律)}'
'''
def play_word(word: str):
    if is_sound_on():
        # echo -n "hello" | espeak
        # echo -n "hello" | say
        Popen(["say", word])
    wd = get_word_def(word)
    if wd:
        print(f"\033[92m{wd.phonetic}\033[0m\n")
        print(wd.paraphrase)
    # else:
    #     print(f"{word}: no definition found")
    return wd
