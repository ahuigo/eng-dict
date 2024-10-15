from store import Store
from struct import unpack
from zlib import decompress
from bs4 import BeautifulSoup
import pdb,json,re,os
from subprocess import getoutput
from tool import is_debug
from typing import List, Any
MAX_DEF_LEN = 1500
words_file = os.getenv("HOME", "/tmp")+'/.words.hash.gz'

class WordDef(dict):
    phonetic: str = ''
    paraphrase: str = ''
    sentences: str = ''
    sentences2: List[Any] = []
    rank = ""
    pattern = ""
    def __init__(self, *args, **kwargs):
        super(WordDef, self).__init__(*args, **kwargs)
        self.__dict__ = self
    def __str__(self):
        self.__dict__['phonetic'] = self.phonetic
        self.__dict__['paraphrase'] = self.paraphrase
        return json.dumps(self, ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

def gen_words():
    from gendict2 import genWordDef2
    print("gen_words 1")
    for word, entry in gen_words_entry():
        wordDef = parserWordXml(entry.decode()) 
        word = str(word.decode())
        yield word, wordDef
    print("gen_words 2")
    for wdf in genWordDef2():
        wordDef = WordDef()
        wordDef.phonetic = wdf.pronunciation
        wordDef.paraphrase = wdf.paraphrase
        wordDef.sentences2 = wdf.sentences
        wordDef.rank = wdf.rank
        wordDef.pattern = wdf.pattern
        yield wdf.word, wordDef

def gen_words_debug():
    if not is_debug(1):
        quit("debug mode 1 only")
    for word, entry in gen_words_entry():
        word = str(word.decode())
        if word != 'A': # type:ignore
            print(word)
            # print(entry.decode())
            wordDef = parserWordXml(entry.decode()) 
            print(wordDef.paraphrase)
            pdb.set_trace()
            # quit()

def gen_words_entry():
    #> https://gist.github.com/josephg/5e134adf70760ee7e49d
    #> Reverse-Engineering Apple Dictionary: https://fmentzer.github.io/posts/2020/dictionary/
    filename = '../langdao-ec-gb/Body.data'
    filename = '/System/Library/AssetsV2/com_apple_MobileAsset_DictionaryServices_dictionaryOSX/9cf76a203397f26625fa0c1e9f594f0da5ad7f68.asset/AssetData/Simplified Chinese - English.dictionary/Contents/Resources/Body.data'
    with open(filename, 'rb') as f:
        f.seek(0x40)
        limit = 0x40 + unpack('i', f.read(4))[0]
        f.seek(0x60)
        while f.tell()<limit:
            sz, = unpack('i', f.read(4))
            buf = decompress(f.read(sz)[8:])

            pos = 0
            while pos < len(buf):
                chunksize, = unpack('i', buf[pos:pos+4])
                pos += 4

                entry = buf[pos:pos+chunksize]
                
                word = re.search(b'd:title="(.*?)"', entry).group(1) # type:ignore
                # word = str(word.decode())
                yield word, entry
                pos += chunksize


def has_class(tag, cls):
    return hasattr(tag, 'attrs') and cls in tag.attrs.get('class',[])

def remove_pinyin(bsnode):
    if hasattr(bsnode, 'find_all'):
        for node in bsnode.find_all(class_="ty_pinyin"):
            node.decompose()

def simple_paraphrase(s:str):
    s = re.sub(r'‹[a-zA-Z, ]+›', '', s.strip())
    s = re.sub(r'«[a-zA-Z, ]+»', '', s)
    s = re.sub(r'\([a-zA-Z, ]+\)', '', s)
    s = re.sub(r'^\s+', '', s)
    s = re.sub(r'\n+', '\n', s)
    # s = re.sub(r'«|»|‹|›|\(|\)', '', s.strip())
    # s = re.sub(r'\b[a-zA-Z]+\b', '', s)
    return s

def parserWordXml(s:str):
    wordDef = WordDef()
    soup = BeautifulSoup(s, 'lxml')
    if soup.body is None:
        return wordDef
    entry = soup.body.find('d:entry')
    for span in entry: # type:ignore
        if 'hwg' in span.attrs.get('class',[]):
            # BrE Phonetic Symbols
            wordDef.phonetic=(span.text)
        else:
            try:
                for child_exp in span.children: # paraphrase list
                    sentences = '' 
                    if child_exp.name is None:
                        sentences = child_exp.text.strip()
                        paraphrase = sentences
                    else:
                        sentences = ''
                        paraphrase = ''
                        for child in child_exp.children:
                            text = child.text.strip()
                            if has_class(child, 'ty_label'):
                                sentences += text+' '
                            elif text:
                                remove_pinyin(child)
                                if has_class(child, 'trg') or has_class(child, 'trgg'): # class="trg" 解释
                                    s = simple_paraphrase(child.text)
                                    paraphrase+= f"\033[95m{s}\033[0m\n"
                                    sentences+= f"\033[95m{s}\033[0m\n"
                                else: # class="exg" 例句
                                    sentences += child.text.strip()+'\n'
                                    # paraphrase = re.sub(r'▸[^\n]+\n', '', sentences)
                    if sentences: 
                        wordDef.paraphrase += paraphrase + "\n" 
                        wordDef.sentences += sentences + "\n" 
                    if len(wordDef.paraphrase)>MAX_DEF_LEN:
                        wordDef.paraphrase+='(too long to skip...)'
                        break 
                if len(wordDef.paraphrase)>MAX_DEF_LEN:
                    break
            except Exception as e:
                print("xml:\n",s)
                raise (e)
    return wordDef


def gen_dict():
    store=Store(db_filepath=words_file)
    if os.path.exists(words_file):
        print("{} exists, skip".format(words_file))
        return
    i = 0
    for word, definition in gen_words():
        store.add_item(word, definition)
        # print(json.dumps(definition))
        # return
        i+=1
        if is_debug(2) and i>1000:
            print("limit 1000")
            pdb.set_trace()
            break
        if i % 10000 == 0:
            print(i)
        if i> 30*10000:
            quit("excceed 30*10000")
    store.save()
    print("test:\n3D: ",store.get('3D'))
    print("Armenian:",store.get('Armenian'))

def get_word_def(word:str):
    if not word:
        return 
    store=Store(db_filepath=words_file)
    d=store.get(word)
    if not d:
        if re.match(r'[a-z]',word):
            d=store.get(word.capitalize())
        else:
            d=store.get(word.lower())
    if d:
        obj = json.loads(d)
        wd = WordDef(**obj)
        # wd.phonetic = obj.get('phonetic','')
        # paraphrase = obj.get('paraphrase','')
        # wd.paraphrase = re.sub(r'▸[^\n]+\n', '', paraphrase)
        # wd.paraphrase = re.sub(r'\n\n', '\n', wd.paraphrase)
        # wd.sentences = paraphrase
        return wd
    
def is_sound_on():
    self = is_sound_on
    if not hasattr(self, "c"):
        if "✅" in os.getenv("PROMPT", ""):  # only check my own PROMPT
            output = getoutput("system_profiler SPAudioDataType")
            kwords = ["Headphones", "USB-C HEADSET"]
            self.c = any(kword in output for kword in kwords)
        else:
            self.c = True
    return self.c

if __name__ == '__main__':
    if is_debug(1):
        gen_words_debug()
    else:
        gen_dict()
