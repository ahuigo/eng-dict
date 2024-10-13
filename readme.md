# 词典工具
本库提供了以下功能:
1. 词典库：langdao词典、coca6000 词汇、Apple中文词典hash表
2. store.py 简单的hash持久化词典数据库实现(使用gzip 压缩)
3. gendict.py 将mac osx 内的字典，转换成hash数据库
4. gword.py 查找单词、自动发单（仅支持mac osx）
5. traslate.py 自动翻译

## 安装
安装：

    cd ~ && git clone https://github.com/ahuigo/eng-dict
    cd eng-dict && make clean && make install

如果你的python 比较低，升级到　Python >= 3.11

    brew update && brew upgrade python

简化别名

    alias t=t.py

## 查词+翻译
翻译：

    $ t.py '翻译这句话！'
      Translate this sentence!

    $ t.py 'translate this word'
    翻译这个词

如果你输入的是一个英文单词，就会进入查单词模式： 它会自动发音(仅mac)+音标输出

    $ t.py rubber
    rubber  | BrE ˈrʌbə, AmE ˈrəbər |  

    A. noun
    ① uncountable (substance) 橡胶 xiàngjiāo
    ▸ a rubber ball/hose 皮球/橡胶软管

# 词典库
两种下载方法：
1. baidu pan　下载
链接: https://pan.baidu.com/s/1u12RFO4hSHzbdlOR40rsyg?pwd=5qx9 提取码: 5qx9 
2. gh release 下载：
https://github.com/ahuigo/eng-dict/releases/tag/v0.1.0


## langdao 词典
mac dictionary 制作方法
1. 制作文章1：https://www.zhihu.com/question/20428599
2. [使用文章2: medium](https://medium.com/@ahuigo/mac-osx%E4%B8%8B%E5%A5%BD%E7%94%A8%E7%9A%84%E8%AF%8D%E5%85%B8%E5%B7%A5%E5%85%B7-8b07b7c8a88)
3. 使用方法：https://sspai.com/post/43155

langdao dict for mac dictionary app:

    # 词典库被安装到 ~/Library/Dictionaries/langdao-ec-gb.dictionary/
    tar xzvf langdao.tgz -C ~/

## cocal6000.txt 词汇表