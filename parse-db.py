#> https://gist.github.com/josephg/5e134adf70760ee7e49d
#> Reverse-Engineering Apple Dictionary: https://fmentzer.github.io/posts/2020/dictionary/
from struct import unpack
from zlib import decompress
import re
filename = './langdao-ec-gb/Body.data'
filename = '/System/Library/AssetsV2/com_apple_MobileAsset_DictionaryServices_dictionaryOSX/6b98409a6f704b07449c95dead92a7911dba87d6.asset/AssetData/New Oxford American Dictionary.dictionary/Contents/Resources/Body.data'
filename = '/System/Library/AssetsV2/com_apple_MobileAsset_DictionaryServices_dictionaryOSX/ce8cda23e99d8fc3f655ad23fac865041c88cff6.asset/AssetData/Simplified Chinese - English.dictionary/Contents/Resources/Body.data'
f = open(filename, 'rb')

def gen_entry():
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
            
            title = re.search(b'd:title="(.*?)"', entry).group(1)
            yield title, entry.decode()
            pos += chunksize

i = 0
for word, definition in gen_entry():
    print(word)
    i+=1
    print(definition)
    if i> 1000:
        break
