#!/usr/bin/env python3
import sys, os
from gendict import get_word_def
from subprocess import getoutput, call, Popen


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
        Popen(["say", word])
    wd = get_word_def(word)
    if wd:
        print(f"\033[92m{wd.phonetic}\033[0m\n")
        print(wd.explanation)
    # else:
    #     print(f"{word}: no definition found")
    return wd
