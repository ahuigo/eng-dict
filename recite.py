#!/usr/bin/env python3
import sys, termios,os,select
from gendict import get_word_def 
from subprocess import getoutput,call

def getch(timeout=20):
    fd = sys.stdin.fileno()
    orig = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~termios.ICANON
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0

    try:
        termios.tcsetattr(fd, termios.TCSAFLUSH, new)
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            return sys.stdin.read(1)
        else:
            print("Timeout")
            return None
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, orig)

def has_headphone():
    from subprocess import getoutput
    output = getoutput("system_profiler SPAudioDataType")
    return "Headphones" in output

class WordsRepo():
    words = ["tactic", "tackle","twist"]
    def __init__(self):
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.words):
            result = self.words[self.index]
            self.index += 1
            return result
        else:
            raise StopIteration


def recite():
    if not has_headphone():
        quit("please plug in headphones")
    words = WordsRepo()
    for word in words:
        call(f'say "{word}"', shell=True)
        print(word)
        char = getch(20)
        match char:
            case 'j':
                print("j. show the word's definition")
                wd = get_word_def(word)
                if wd:
                    print(wd.explanation)
                else:
                    print(f"{word}: no definition found")
            case ' ':
                print("you have passed this word")
            case None:
                print("timeout")
            case _:
                print(f"You entered: {char}")
if __name__ == '__main__':
    recite()
