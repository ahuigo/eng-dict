from store import Store
from struct import unpack
from zlib import decompress
from bs4 import BeautifulSoup
import pdb,json,re,os
from subprocess import getoutput
from tool import is_debug
MAX_DEF_LEN = 1500
words_file = os.getenv("HOME", "/tmp")+'/.words.hash.gz'

def gen_words():
    for word, entry in gen_words_entry():
        wordDef = parserWordXml(entry.decode()) #word.explanation
        word = str(word.decode())
        yield word, wordDef

def gen_words_debug():
    if not is_debug(1):
        quit("debug mode 1 only")
    for word, entry in gen_words_entry():
        word = str(word.decode())
        if word != 'A': # type:ignore
            print(word)
            # print(entry.decode())
            wordDef = parserWordXml(entry.decode()) #word.explanation
            print(wordDef.explanation)
            pdb.set_trace()
            # quit()

def gen_words_entry():
    #> https://gist.github.com/josephg/5e134adf70760ee7e49d
    #> Reverse-Engineering Apple Dictionary: https://fmentzer.github.io/posts/2020/dictionary/
    filename = '../langdao-ec-gb/Body.data'
    filename = '/System/Library/AssetsV2/com_apple_MobileAsset_DictionaryServices_dictionaryOSX/6b98409a6f704b07449c95dead92a7911dba87d6.asset/AssetData/New Oxford American Dictionary.dictionary/Contents/Resources/Body.data'
    filename = '/System/Library/AssetsV2/com_apple_MobileAsset_DictionaryServices_dictionaryOSX/ce8cda23e99d8fc3f655ad23fac865041c88cff6.asset/AssetData/Simplified Chinese - English.dictionary/Contents/Resources/Body.data'
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

class WordDef(dict):
    phonetic: str = ''
    explanation: str = ''
    def __init__(self, *args, **kwargs):
        super(WordDef, self).__init__(*args, **kwargs)
        self.__dict__ = self
    def __str__(self):
        self.__dict__['explanation'] = self.explanation
        self.__dict__['phonetic'] = self.phonetic
        return json.dumps(self, ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

def has_class(tag, cls):
    return hasattr(tag, 'attrs') and cls in tag.attrs.get('class',[])

def remove_pinyin(bsnode):
    if hasattr(bsnode, 'find_all'):
        for node in bsnode.find_all(class_="ty_pinyin"):
            node.decompose()

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
                for child_exp in span.children: # explanation list
                    explanation = '' 
                    if child_exp.name is None:
                        explanation = child_exp.text.strip()
                    else:
                        explanation = ''
                        for child in child_exp.children:
                            text = child.text.strip()
                            if has_class(child, 'ty_label'):
                                explanation += text+' '
                            elif text:
                                remove_pinyin(child)
                                if has_class(child, 'trg') or has_class(child, 'trgg'): # class="trg" 解释
                                    explanation+= f"\033[95m{child.text.strip()}\033[0m\n"
                                else: # class="exg" 例句
                                    explanation += child.text.strip()+'\n'
                        # print("debug exp:", explanation)
                        # pdb.set_trace()

                    if explanation: 
                        wordDef.explanation += explanation + "\n" 
                    if len(wordDef.explanation)>MAX_DEF_LEN:
                        wordDef.explanation+='(too long to skip...)'
                        break 
                if len(wordDef.explanation)>MAX_DEF_LEN:
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
        #print(word)
        #print(definition)
        i+=1
        if is_debug(2) and i>1000:
            print("limit 1000")
            pdb.set_trace()
            break
        if i % 10000 == 0:
            print(i)
        if i> 22*10000:
            quit("excceed 22*10000")
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
        wd = WordDef()
        wd.explanation = obj.get('explanation','')
        wd.phonetic = obj.get('phonetic','')
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
