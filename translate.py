#!/usr/bin/env python3
import sys
import argparse
import requests,re,json
from subprocess import getoutput,check_output
import gword

def read_input():
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    return '\n'.join(lines)

def isChinese(text)->bool:
    pattern = re.compile(r'[\u4e00-\u9fa5]')
    # fullmatch(^search$)
    return bool(pattern.search(text))

def getQuery()->str:
    parser = argparse.ArgumentParser()
    parser.add_argument('query', nargs='*', default='')
    args = parser.parse_args()
    query = ''
    if args.query:
        query = " ".join(args.query)
    else:
        if not sys.stdin.isatty():
            query = read_input()
    query = query.strip()
    if not query:
        quit("Usage: python3 translate.py <query>")
    return query

def trans_gpt(query:str):
    url = 'https://mygpt.com.local/api/chat-process'
    headers = {
            "Content-Type":"application/json"
    }
    lang =  'English' if isChinese(query) else '中文'
    data = {
        'model': 'gpt-3.5-turbo', #"gpt-4" 和 "gpt-3.5-turbo"
        'options': {
            # 'parentMessageId': '' # session's last message id
        },
        'prompt': f"翻译以下内容为 {lang}:\n"+query
    }

    resp= requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    print("code:",resp.status_code)
    print(resp.text)
    datastr = resp.text.strip().split('\n')[-1]
    data = json.loads(datastr)
    # data['parentMessageId']
    try:
        output = data['text']
        print(output)
    except Exception as e:
        print(data)

""""
https://github.com/soimort/translate-shell
"""
def trans_shell(query:str):
    lang =  ':@en' if isChinese(query) else ':@zh'
    if lang == ':@zh' and re.fullmatch(r'[a-zA-Z]+', query):
        gword.show_word(query)
        quit()
    #print("trans",lang, "-b", query)
    cmd = f"trans {lang} -show-original n -show-translation n  -show-prompt-message n  -show-languages n".split()
    # print(*cmd, query)
    # google / bing/ ...
    ans = check_output([*cmd, "-e", "google", query]).decode()
    return ans

def main():
    query = getQuery()
    ans = trans_shell(query)
    print(ans)

if __name__ == "__main__":
    main()
