#!/usr/bin/env python3
import sys, os, json, time,re, pdb
from typing import List, Dict
from pathlib import Path
from gendict import get_word_def, is_sound_on
from subprocess import getoutput, call,Popen
from tool import getch, clear_screen,debug_print
from translate import trans_shell


source_dir = Path(__file__).resolve().parent.__str__()
data_dir = source_dir+"/data"
words_path = f"{data_dir}/words.txt"
words_statis_path = f"{data_dir}/statis.txt"
word_display_timeout = 30

def is_debug(mode=None):
    debug = os.getenv("DEBUG", False)
    if mode is None:
        return debug
    return debug and str(mode) == debug

class Record(dict):
    word = ""
    updated_at = 0
    succ = 0
    fail = 0
    succ0 = 0  # today(不管时间)
    succ1 = 0
    succ2 = 0
    succ7 = 0
    succ15 = 0
    succ30 = 0

    def __init__(self, *args, **kwargs):
        self.update(
            {
                "updated_at": 0,
                "succ": 0,
                "fail": 0,
                "succ1": 0,
                "succ2": 0,
                "succ7": 0,
                "succ15": 0,
                "succ30": 0,
            }
        )
        self.update(kwargs)
        self.__dict__ = self

    def is_need_recite(self):
        now = time.time()
        if not self.updated_at:
            return True
        if self.succ1 < 2:
            return True
        elif self.succ2 < 2:
            return now - self.updated_at >= 1 * 86400
        elif self.succ7 < 2:
            return now - self.updated_at >= 5 * 86400
        elif self.succ15 < 2:
            return now - self.updated_at >= (15 - 7) * 86400
        elif self.succ30 < 2:
            return now - self.updated_at >= (30 - 15) * 86400
        else:
            return False

    def pass_word(self):
        now = int(time.time())
        last_updated_at = self.updated_at
        if last_updated_at == 0:
            last_updated_at = now
        self.succ += 1
        self.succ0 += 1
        if self.succ0 < 2:
            return
        if self.succ1 < 2:
            self.succ1 = 2
        elif self.succ2 < 2:
            if now - last_updated_at >= 1 * 86400:
                return
            self.succ2 = 2
        elif self.succ7 < 2:
            if now - last_updated_at >= 5 * 86400:
                return
            self.succ7 = 2
        elif self.succ15 < 2:
            if now - last_updated_at >= 8 * 86400:
                return
            self.succ15 = 2
        elif self.succ30 < 2:
            if now - last_updated_at >= (30 - 15) * 86400:
                return
            self.succ30 = 2
        self.updated_at = now


class WordsStatis:
    # meta
    sort = "asc"
    last_index = 0
    myrecords: Dict[str, Record] = {}
    last_record_data = None

    def __init__(self):
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        if not os.path.exists(words_statis_path):
            return
        with open(words_statis_path, "r+") as fp:
            line = fp.readline().strip()
            if line:
                meta = json.loads(line)
                self.sort = meta.get("sort", "asc")
                self.last_index = int(meta.get("last_index", 0))
                print("sort: ", self.sort, "last_index: ", self.last_index)
            for line in fp.readlines():
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                self.myrecords[record["word"]] = Record(**record)

    def is_need_recite(self, word):
        if word not in self.myrecords:
            return True
        return self.myrecords[word].is_need_recite()

    def pass_word(self, word):
        if word not in self.myrecords:
            self.myrecords[word] = Record(word=word)
        self.last_record_data = {**self.myrecords[word]}
        self.myrecords[word].pass_word()

    def undo(self):
        record_data = self.last_record_data
        if record_data:
            record = Record(**record_data)
            word = record_data["word"]
            self.myrecords[word] = record
        self.last_record_data = None

    def save(self, last_index):
        with open(words_statis_path, "w+") as fp:
            fp.write(json.dumps({"sort": self.sort, "last_index":last_index}) + "\n")
            for word, record in self.myrecords.items():
                fp.write(json.dumps(record) + "\n")


class WordsRepo:
    if not os.path.exists(words_path):
        quit("你需要先创建一个单词文件:{}\n".format(words_path))

    words: List[str] = []
    statis = WordsStatis()

    def __init__(self):
        # 1. init words
        words1 = (word.strip() for word in open(words_path))
        self.words = list(filter(lambda x: re.match(r'[a-zA-Z]',x), words1))
        self.register_quit_handler()
        # 2. init set index
        self.index = self.statis.last_index
        if self.index < 0:
            self.index = 0
            self.statis.sort = "asc"
        elif self.index >= len(self.words):
            self.index = len(self.words) - 1
            self.statis.sort = "desc"

    def __iter__(self):
        return self

    def __next__(self):
        count = 0 
        max_count = len(self.words)
        while True:
            count += 1
            if count > max_count: raise StopIteration
            word = self.next()
            if self.statis.is_need_recite(word):
                return word

    def __prev__(self):
        try:
            count = 0 
            max_count = len(self.words)
            word = self.prev() # revert self.index (revert to current word)
            while True:
                count += 1
                if count > max_count: raise StopIteration
                word = self.prev()
                if self.statis.is_need_recite(word):
                    return word
        except StopIteration:
            pass

    def undo(self):
        self.statis.undo()
        try:
            self.__prev__()
        except StopIteration:
            print("no more undo prev words")
            pass

    def sort_toggle(self):
        sort = self.statis.sort
        self.statis.sort = "asc" if sort == "desc" else "desc"
        print("toggle sort: ", self.statis.sort)

    def register_quit_handler(self):
        import signal
        def handler(signum, frame):
            self.save()
            sys.exit(0)
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGQUIT, handler)

    def save(self):
        self.__prev__()
        self.statis.save(self.index)
        print("schedule is saved")


    def current(self):
        if self.index < len(self.words) and self.index >= 0:
            word = self.words[self.index]
            return word
        else:
            # debug_print("word0: ", "no more words", self.index, self.statis.sort)
            raise StopIteration

    def next(self):
        word = self.current()
        if self.statis.sort == "asc":
            self.index += 1
            if self.index >= len(self.words):
                self.index = 0
        else:
            self.index -= 1
            if self.index < 0:
                self.index = len(self.words) - 1
        return word

    def prev(self): # 其实是current
        # debug_print("prev word1: ", word, self.index, self.statis.sort)
        if self.statis.sort == "asc":
            self.index -= 1
            if self.index < 0:
                self.index = len(self.words) - 1
        else:
            self.index += 1
            if self.index >= len(self.words):
                self.index = 0
        word = self.current()
        # debug_print("prev word2: ", self.index)
        return word

def set_word_display_timeout():
    global word_display_timeout
    try:
        word_display_timeout = int(input("设置单词显示时间(秒): ").strip())
    except Exception as e:
        print("invalid input")
    if word_display_timeout <1:
        word_display_timeout = 1

def say_explanation(s:str):
    for index,key in enumerate(['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩']):
        s= re.sub(key,f'', s)
    s = re.sub(r'\x1b\[9\dm', '', s)
    s = re.sub(r'\x1b\[0m', '', s)
    s = re.sub(r'«|»|‹|›|\(|\)', '', s)
    # s = re.sub(r'‹[\w, ]+›', '', s)
    # s = re.sub(r'«[\w, ]+»', '', s)
    s = re.sub(r'\b[a-zA-Z]+\b', '', s)
    p = Popen(['say','-v', 'Meijia', s])
    return p

def display_word_def(word):
    # clear_screen()
    wd = get_word_def(word)
    if wd:
        process = say_explanation(wd.paraphrase)
        print(f"=====query mode: {word} ====\n",wd.paraphrase)
        print("press `s` to show sentence")
        if getch(200) == "s":
            print(wd.sentences)
            print("press any key to quit query mode")
            getch(200)
        process.terminate()

    else:
        print(f"{word}: no definition found; press any key to quit")
        getch(200)

def print_help():
    s= ("h: help"
"""
    <Ctrl+c>: quit and save progress
    s: sort toggle 
    i: input word/scentence to translate
    t: set display word timeout
    d: display word definition
    <space>: pass word
    u: undo last passed word
    n: next word
    p: previous word

Press any key to exit help
""")
    print(s, end="")
    w = getch(1000)
    print("w: ", w)

def translate():
    query = input("Input something to translate: ").strip()
    print(trans_shell(query))

def recite():
    # global word_display_timeout
    if not is_sound_on():
        quit("please plug in headphones")
    wordsRepo = WordsRepo()
    for word in wordsRepo:
        clear_screen()
        Popen(f'say "{word}"', shell=True)
        print("next index:", wordsRepo.index, f"interval: {word_display_timeout}s")
        char = getch(word_display_timeout)
        match char:
            case "h":
                print_help()
            case "i":
                translate()
            case "t":
                set_word_display_timeout()
            case "d":
                display_word_def(word)
            case "s":
                wordsRepo.sort_toggle()
            case " ":
                print("passed word: " + word)
                wordsRepo.statis.pass_word(word)
            case "u":
                wordsRepo.statis.undo()
            case 'n':
                pass
            case "p":
                wordsRepo.__prev__()
            case None:
                pass
            case _:
                print(f"\ninvalid action: {char}")
                print_help()
    wordsRepo.save()
    print("done")


if __name__ == "__main__":
    recite()
