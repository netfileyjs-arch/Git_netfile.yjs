# -*- coding: utf-8 -*-
"""
단독 실행용 웹페이지(HTML 파일 하나) 만들기

standalone_template.html 에 dictionary.txt 와 keywords.txt 를 넣어서
'파일명_키워드_필터.html' 을 만듭니다. 이 HTML 은 Python 없이 더블클릭만으로 동작합니다.

사용법:
    python build_standalone.py
"""

import json
import os

from filter_core import BASE_DIR, DICTIONARY_PATH

TEMPLATE_PATH = os.path.join(BASE_DIR, 'standalone_template.html')
KEYWORDS_PATH = os.path.join(BASE_DIR, 'keywords.txt')
OUTPUT_PATH = os.path.join(BASE_DIR, '파일명_키워드_필터.html')
PLACEHOLDER = '/*__DEFAULTS__*/'


def read_file(path):
    if not os.path.exists(path):
        return ''
    with open(path, encoding='utf-8') as f:
        return f.read()


def main():
    defaults = {'keywords': read_file(KEYWORDS_PATH).strip(), 'dictionary': read_file(DICTIONARY_PATH)}
    # <script> 안에 넣으므로 '</' 가 태그를 닫지 않게 처리
    data = json.dumps(defaults, ensure_ascii=False).replace('</', '<\\/')
    html = read_file(TEMPLATE_PATH)
    if PLACEHOLDER not in html:
        raise SystemExit(f'템플릿에 {PLACEHOLDER} 가 없습니다: {TEMPLATE_PATH}')
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html.replace(PLACEHOLDER, data))
    print(f'저장: {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
