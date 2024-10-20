# -*- coding: utf-8 -*-
import zlib
import json
from typing import List, Any

##################################################################
# refer: https://github.com/ChestnutHeng/Wudao-dict/tree/master/wudao-dict/dict
##################################################################
class MywordDef2(dict):
    word = ""
    pronunciation = ""

    rank = ""
    pattern = ""

    paraphrase = ""
    sentences: List[Any] = []
    def __init__(self, *args, **kwargs):
        super(MywordDef2, self).__init__(*args, **kwargs)
        self.__dict__ = self

class WdDicts:
    def iter(self):
        self.FILE_NAME = './dist/en.z'
        self.INDEX_FILE_NAME = './dist/en.ind'
        self.__index_dict = {}
        with open(self.INDEX_FILE_NAME, 'r') as f:
            lines = f.readlines()
            prev_word, prev_no = lines[0].split('|')
            for v in lines[1:]:
                word, no = v.split('|')
                self.__index_dict[prev_word] = (int(prev_no), int(no) - int(prev_no))
                # print(prev_word,self.__index_dict[prev_word] )
                prev_word, prev_no = word, no
            # self.__index_dict[word] = (int(no), f.tell() - int(no))
            # print(word,self.__index_dict[word])

        with open(self.FILE_NAME, 'rb') as f:
            for word,word_offset in self.__index_dict.items():
                r = self.get_word_info(f, word_offset)
                yield r

    # return strings of word info
    def get_word_info(self,f, word_offset):
        f.seek(word_offset[0])
        bytes_obj = f.read(word_offset[1])
        str_obj = zlib.decompress(bytes_obj).decode('utf8')
        list_obj = str_obj.split('|')
        word = MywordDef2()
        word.word = list_obj[0]
        word.pronunciation = ""
        if list_obj[3]:
            word.pronunciation += 'BrE '+list_obj[3] + ', '
        if list_obj[2]:
            word.pronunciation += 'AmE '+list_obj[2]
        if list_obj[4]:
            word.pronunciation += list_obj[4]
        if word.pronunciation:
            word.pronunciation = f"|{word.pronunciation}|"
        word.paraphrase = '\n'.join(json.loads(list_obj[5])).strip()
        word.rank = list_obj[6]
        word.pattern = list_obj[7]
        word.sentences = parseSentence(list_obj[8])
        return word

def parseSentence(s:str):
    for i in range(0, 3):
        try:
            stsGroups = json.loads(s)
            sentences = []
            for stsGroup in stsGroups:
                obj = {
                    'type': "",
                    'definition': stsGroup[0],
                    'examples' : [] #stsGroup[2]
                }

                if len(stsGroup)>1:
                    obj['type'] = stsGroup[1]
                if len(stsGroup)>2:
                    obj['examples'] = stsGroup[2]
                sentences.append(obj)
            return sentences
        except Exception as e:
            if i == 0:
                s += '"]]'
                continue
            print('obj:',s,i)
            raise e
def genWordDef2():
    wds = WdDicts()
    return wds.iter()

if __name__ == '__main__':
    i = 0
    for wd in genWordDef2():
        i += 1
        print(json.dumps(wd))
        # if i > 10: quit()

