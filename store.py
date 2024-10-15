from typing import Any,Dict,List, Tuple
import hashlib,pdb,struct,os,sys,gzip,re
from enum import Enum
from io import BufferedReader
from gzip import GzipFile

def isDebug(mode=3):
    debug = os.getenv("DEBUG", False)
    if mode is None:
        return debug
    return debug and str(mode) == debug
def debug(*args):
    if isDebug():
        print(*args)

default_db_path = os.getenv("HOME", "/tmp")+'/.words.hash.gz'
KEY_LEN = 4 # 4 bytes
VAL_POS_NULL = b'\xff'*KEY_LEN
class Store():
    dict: Dict[str,str] = {}
    header_length = 20 # 20 bytes
    db_filepath:str = ''
    vdata:bytearray = bytearray()
    kdata:List[bytes] = [] #　store key pointer(32 bytes)
    # header
    data_pos = 0 # data offset = header_length + key_num*KEY_LEN

    def __init__(self, db_filepath:str = default_db_path):
        self.db_filepath = db_filepath

    def add_item(self, key:str, val: Any):
        v = val.__str__()
        self.dict[key] = v
    
    def hash_key(self,key:str, hash_len:int):
        h = hashlib.md5()
        h.update(key.encode())
        s = int(h.hexdigest(), 16)
        return s % hash_len

    def generate_hash_index(self, key:str, hash_key_num:int):
        kIndex = self.hash_key(key, hash_key_num)
        loop = 1
        while True:
            debug(f"generate key index:{key}=>{kIndex}",self.kdata)
            # 1. 如果没有hash 冲突: quit
            if self.kdata[kIndex] == VAL_POS_NULL:
                break
            debug("current_val_pos:",self.kdata[kIndex])
            # 2. 如果有hash 冲突: # data 的第一个字节标记有下一个key
            val_pos_bytes = self.kdata[kIndex]
            val_pos = int.from_bytes(val_pos_bytes,'big')
            self.vdata[val_pos] = 1

            # 3. 判断key是否相等(word已经存在)
            record_len = int.from_bytes(self.vdata[val_pos+1:val_pos+3],'big')
            start, end = val_pos+3, val_pos+3+record_len

            word2 = self.vdata[start:end].split(b':',1)[0].decode()
            if word2 == key:
                return -1

            # 4. kIndex 指向下一个空位
            kIndex+=1
            if kIndex >= hash_key_num:
                loop += 1
                if loop > 2: raise Exception('hash index overflow')
                kIndex = 0
        return kIndex

    def serialize_data(self, has_next_key:bool, k:str, v:str):
        # has_next_key(1byte)| data_length(2bytes)| key:value
        d = f'{k}:{v}'.encode()
        if len(d) >= 2**16:
            quit(f'fatal: {k} data length({len(d)}) >= 2**16')
        if has_next_key:
            return b'\x01'+len(d).to_bytes(2,'big')+d
        else:
            return b'\x00'+len(d).to_bytes(2,'big')+d

        
    def save(self):
        print(f"1. init save file {self.db_filepath}")
        key_num = len(self.dict)
        hash_key_num = key_num*2
        self.kdata = [VAL_POS_NULL]*hash_key_num
        if key_num == 0:
            quit(f'no data to save')
        if hash_key_num >= 2**(KEY_LEN*8) :
            quit(f'fatal: hash_key_num({hash_key_num}) >= 2**{KEY_LEN*8}')

        print("2. index + serialize data")
        i = 0
        for k,v in self.dict.items():
            i+=1
            if i % 10000 == 0: print(i)
            debug(f"------key: {k}-----")
            key_index = self.generate_hash_index(k, hash_key_num) 
            if key_index < 0: # word already exists
                continue
            val_pos = len(self.vdata)
            serialize_val = self.serialize_data(False, k,v)
            self.vdata.extend(serialize_val)
            debug("serialize_key_index:", key_index)
            debug("serialize_val_pos:", val_pos)
            debug("serialize_val:",serialize_val)
            debug("vdata:", self.vdata)
            try:
                self.kdata[key_index] = val_pos.to_bytes(KEY_LEN,'big')
            except Exception as e:
                print(f'val_pos:{val_pos},{KEY_LEN}')
                raise e
        print("3. ===write to file ========")
        '''  
        header: data_pos(4 bytes) + key_num(4 bytes) + (12 bytes other)
        key_data: key_index=> val_pos (4 bytes= 32bit)
        value_data: has_next_key(1byte)| data_length(2bytes)| key:value
        '''
        with gzip.open(self.db_filepath,'wb') as fp:
            # 1. write header: data_pos_offset(4 bytes) + hash_key_num(4 bytes) + (12 bytes other)
            val_pos = self.header_length + len(self.kdata)*KEY_LEN
            headers = struct.pack('>II',val_pos, hash_key_num) # 8 bytes
            debug(f"header: {self.header_length} +key_num:{len(self.kdata)} * {KEY_LEN} ")
            debug("header data:",headers)
            fp.write(headers+ b'\x00'*(self.header_length - len(headers)))
            # 2. write keys
            for val_pos in self.kdata:
                if val_pos == VAL_POS_NULL:
                    fp.write(VAL_POS_NULL)
                else:
                    debug("data_pos:", int.from_bytes(val_pos,'big'))
                    fp.write(val_pos)
            # 3. write values
            fp.write(self.vdata)
            # 4. parse vdata
            if isDebug():
                self.debug_loopVdata(self.vdata)

    def debug_loopVdata(self, vdata: bytearray):
        print("-----------loopVdata:-----------------")
        pos = 0
        count = 0 
        while True:
            count += 1
            if count > 2:
                break
            val_len = int.from_bytes(vdata[pos+1:pos+3],'big')
            val = vdata[pos+3:pos+3+val_len]

            print("has_key:",(vdata[pos]))
            print("flag-len:",vdata[pos:pos+3])
            print("val_len:",val_len)
            print("val(%s):" % val)
            pos += 3+val_len

        print("-----------------------------------")
    '''  
    header: data_pos(4 bytes) + key_num(4 bytes) + (12 bytes other)
    key_data: key_index => val_pos
    value_data: has_next_key(1byte)| data_length(2bytes)| key:value
    '''
    def debug_first_word(self):
        with gzip.open(self.db_filepath,'rb') as fp:
            # 1. header: data pos(4bytes)
            data_pos = int.from_bytes(fp.read(4),'big')

            # 2. first word pointer
            fp.seek(self.header_length)
            data_pointer = int.from_bytes(fp.read(KEY_LEN), 'big') + data_pos

            # has_next_key(1)| data_length(2)| key:value
            # 3. parse data
            fp.seek(data_pointer+1)
            data_len = int.from_bytes(fp.read(2),'big')
            data_bytes = fp.read(data_len)
            print(data_bytes)
            pdb.set_trace()

    def get_fp_val_pos_by_key_index(self, fp:GzipFile|BufferedReader, keyIndex:int):
        # val_pos = self.kdata[kIndex]
        fp.seek(keyIndex*KEY_LEN + self.header_length)
        pos_bytes = fp.read(KEY_LEN)
        if pos_bytes == VAL_POS_NULL:
            return -1
        pos = int.from_bytes(pos_bytes,'big')
        return pos


    def get_fp_keyval(self, fp:GzipFile|BufferedReader, key:str, hash_key_num:int):
        kIndex = self.hash_key(key, hash_key_num)
        count = 0
        max_count = 10
        while True:
            count += 1
            if count >= max_count:
                quit(f"find_key({key}): loop too many times>= {max_count}")
            val_pos = self.get_fp_val_pos_by_key_index(fp, kIndex)
            if val_pos == -1:
                return None,None
            has_next, k,v= self.get_record_by_pos(fp, val_pos)
            # 如果key相等(没有冲突)，返回p
            if k== key:
                return k,v
            # 如果key不相等(有冲突)，就找下一个空位
            if not has_next:
                return None, None
            kIndex += 1
            if kIndex >= hash_key_num:
                kIndex = 0

    # has_next_key(1)| data_length(2)| key:value
    def get_record_by_pos(self,fp:GzipFile|BufferedReader, val_pos:int):
        fp.seek(self.data_pos+val_pos)
        item = fp.read(3)
        has_next_key = bool(item[0])
        # debug('has_next_key:',has_next_key)
        length = int.from_bytes(item[1:3],'big')
        key, value = fp.read(length).decode().split(':',1)
        return has_next_key, key,value

    def get(self, key):
        if not os.path.exists(self.db_filepath):
            quit(f"请先用gendict.py 生成本地字典文件: ({self.db_filepath}) ")
        rawdb_filepath = self.db_filepath
        if rawdb_filepath.endswith('.gz'):
            rawdb_filepath = rawdb_filepath[:-3]
            if not os.path.exists(rawdb_filepath):
                # gunzip -c words.hash.gz > words.hash
                import shutil
                with gzip.open(self.db_filepath, 'rb') as f_in:
                    with open(rawdb_filepath, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

        with open(rawdb_filepath,'rb') as fp:
            # 1. read header: data_pos(4 bytes) + key_num(4 bytes) + (12 bytes other)
            headers = fp.read(self.header_length)
            self.data_pos = int.from_bytes(headers[0:4],'big')
            hash_key_num = int.from_bytes(headers[4:8],'big')
            # 2. get key value from file
            _, value = self.get_fp_keyval(fp, key, hash_key_num)
            return value
    