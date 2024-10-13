#!/usr/bin/env python3
import sys, os, json, time,re, pdb
from typing import List, Dict
from gendict import get_word_def, is_sound_on
from subprocess import getoutput, call,Popen
from tool import getch, clear_screen,debug_print


data_dir = "./data"
words_path = f"{data_dir}/words.txt"
words_statis_path = f"{data_dir}/words-statis.txt"
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
                if self.last_index < 0 and self.sort == "desc":
                    self.last_index = 0
                    self.sort = "asc"
                print("sort: ", self.sort)
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
        self.index = 0
        words1 = (word.strip() for word in open(words_path))
        self.words = list(filter(lambda x: re.match(r'[a-zA-Z]',x), words1))
        self.register_quit_handler()

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            word = self.next()
            if self.statis.is_need_recite(word):
                return word

    def __prev__(self):
        word = self.prev() # revert self.index (让index 指向当前单词)
        while True:
            word = self.prev()
            if self.statis.is_need_recite(word):
                return word

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
        self.statis.save(self.index)


    def current(self):
        if self.index < len(self.words) and self.index >= 0:
            word = self.words[self.index]
            return word
        else:
            debug_print("word0: ", "no more words", self.index, self.statis.sort)
            raise StopIteration

    def next(self):
        word = self.current()
        if self.statis.sort == "asc":
            self.index += 1
        else:
            self.index -= 1
        return word

    def prev(self):
        word = self.current()
        if self.statis.sort == "asc":
            self.index -= 1
        else:
            self.index += 1
        return word



def set_word_display_timeout():
    global word_display_timeout
    input("设置单词显示时间(秒): ").strip()
    word_display_timeout = int(word_display_timeout)

def display_word_def(word):
    # clear_screen()
    wd = get_word_def(word)
    if wd:
        print(wd.explanation)
    else:
        print(f"{word}: no definition found")
    print("press any key to continue")
    getch(200)

def print_help():
    s= ("h: help"
"""
    s: sort toggle 
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

def recite():
    if not is_sound_on():
        quit("please plug in headphones")
    wordsRepo = WordsRepo()
    for word in wordsRepo:
        Popen(f'say "{word}"', shell=True)
        print(word, wordsRepo.index)
        char = getch(word_display_timeout)
        match char:
            case "h":
                print_help()
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


if __name__ == "__main__":
    recite()
