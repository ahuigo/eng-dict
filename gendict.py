from store import Store
from struct import unpack
from zlib import decompress
from bs4 import BeautifulSoup
import pdb,json,re,os
MAX_DEF_LEN = 1500
words_file = os.getenv("HOME", "/tmp")+'/.words.hash'

def gen_words():
    for word, entry in gen_words_entry():
        wordDef = parserWordXml(entry.decode()) #word.explanation
        word = str(word.decode())
        yield word, wordDef

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

def parserWordXml(s:str):
    wordDef = WordDef()
    soup = BeautifulSoup(s, 'lxml')
    if soup.body is None:
        return wordDef
    for span in soup.body.find('d:entry'): # type:ignore
        # pdb.set_trace()
        if 'hwg' in span.attrs.get('class',[]):
            # BrE Phonetic Symbols
            wordDef.phonetic=(span.text)
        else:
            try:
                for child in span.children:
                    if child.name is None:
                        wordDef.explanation = child.text.strip()
                        continue
                    for child in child.children:
                        text = child.text.strip()
                        if hasattr(child, 'attrs') and 'ty_label' in child.attrs.get('class',[]):
                            wordDef.explanation+=text + ' '
                        elif text:
                            wordDef.explanation+=text+'\n'
                            # explanations: class="trg"
                            # example: class="exg"
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
        if i % 10000 == 0:
            print(i)
        if i> 2200*(100):
            break
    store.save()
    print("test:\narmistice: ",store.get('armistice'))
    print("Armenian:",store.get('Armenian'))

def get_word_def(word:str):
    store=Store(db_filepath=words_file)
    d=store.get(word)
    if d:
        obj = json.loads(d)
        wd = WordDef()
        wd.explanation = obj.get('explanation','')
        wd.phonetic = obj.get('phonetic','')
        return wd
    
if __name__ == '__main__':
    gen_dict()
