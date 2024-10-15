#!/usr/bin/env python3
import sys, os
from gendict import get_word_def,is_sound_on, WordDef
from subprocess import getoutput, call, Popen
from tool import getch

'''
play sound:
mpg123 'http://translate.googleapis.com/translate_tts?ie=UTF-8&client=gtx&tl=en&q=remedy'
mpg123 'http://translate.googleapis.com/translate_tts?ie=UTF-8&client=gtx&tl=zh-CN&q={encode(旋律)}'
'''
def play_word(word: str, hide_sentence: bool = False):
    if is_sound_on():
        # echo -n "hello" | espeak
        # echo -n "hello" | say
        Popen(["say", word])
    wd = get_word_def(word)
    if wd:
        if wd.phonetic:
            print(f"\033[92m{wd.phonetic}\033[0m")
        print(wd.paraphrase)
        if hide_sentence:
            print("press s to show sentence")
            action = getch(200)
            if action == 's':
                show_word_sentence(wd)
        else:
            show_word_sentence(wd)

    # else:
    #     print(f"{word}: no definition found")
    return wd

def show_word_sentence(wd: WordDef):
    if wd.sentences2:
        for s in wd.sentences2:
            print(f"----------{s['type']}---------")
            print(s['definition'])
            for ex in s['examples']:
                print("\n".join(ex))
            print("")
    else:
        print(wd.sentences)