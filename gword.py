#!/usr/bin/env python3
import sys, os, re,signal,time
from gendict import get_word_def,is_sound_on, WordDef
from subprocess import getoutput, call, Popen
from multiprocessing import Process
from tool import getch

'''
play sound:
mpg123 'http://translate.googleapis.com/translate_tts?ie=UTF-8&client=gtx&tl=en&q=remedy'
mpg123 'http://translate.googleapis.com/translate_tts?ie=UTF-8&client=gtx&tl=zh-CN&q={encode(旋律)}'
'''
def show_word(word: str, show_sentence: bool = False, timeout=500):
    if is_sound_on():
        # echo -n "hello" | espeak
        # echo -n "hello" | say
        p1 = Popen(["say", word])
    wd = get_word_def(word)
    if wd:
        # p1.wait()
        p2 = say_explanation(wd.paraphrase)
        if wd.phonetic:
            print(f"\033[91m{word} | {wd.rank} {wd.pattern}\033[0m", end=" ")
            print(f"\033[92m{wd.phonetic}\033[0m\n")

        print(wd.paraphrase.strip())
        if not show_sentence:
            print("press s to show sentence")
            action = getch(timeout)
            if action == 's':
                show_word_sentence(wd)
        else:
            show_word_sentence(wd)
        if p2: p2.terminate()
    # else:
    #     print(f"{word}: no definition found")
    return wd

def show_word_sentence(wd: WordDef):
    if wd.sentences2:
        for s in wd.sentences2:
            print(f"----------\033[96m {s['type']} \033[0m---------")
            print(s['definition'])
            for ex in s['examples']:
                print("\n".join(ex))
            print("")
    else:
        print(wd.sentences)



def say_with_time(s:str, wait_pid=0):
    try:
        if wait_pid > 0:
            # call(["sleep", "0.8"])
            os.waitpid(wait_pid, 0)
            pass

        time.sleep(0.2)
        p = Popen(['say','-v', 'Meijia', s])
        def sigHandler(signum, frame):
            p.terminate()
            sys.exit(0)
        signal.signal(signal.SIGTERM, sigHandler)
        p.wait()
    except KeyboardInterrupt:
        pass

def say_explanation(s:str, wait_pid=0):
    if is_sound_on():
        for index,key in enumerate(['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩']):
            s= re.sub(key,f'', s)
        s = re.sub(r'\x1b\[9\dm', '', s)
        s = re.sub(r'\x1b\[0m', '', s)
        s = re.sub(r'«|»|‹|›|\(|\)', '', s)
        s = re.sub(r'\b[a-zA-Z]+\b', '', s)

        child = Process(target=say_with_time, args=[s,])
        child.start()
        return child
