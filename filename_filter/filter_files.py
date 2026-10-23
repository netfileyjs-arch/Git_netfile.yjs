# -*- coding: utf-8 -*-
"""
파일명 키워드 필터 - 명령줄 프로그램

사용법:
    python filter_files.py 파일목록.txt 키워드.txt
    python filter_files.py 파일목록.txt 키워드.txt -o 결과.xlsx
    python filter_files.py 폴더경로 키워드.txt          # 폴더 안 파일명을 직접 읽음
    python filter_files.py 파일목록.txt 키워드.txt --no-translate

키워드 파일은 '/', 줄바꿈, 쉼표 어느 것으로 구분해도 됩니다.
"""

import argparse
import os
import sys

from filter_core import (DICTIONARY_PATH, filter_filenames, load_dictionary,
                         parse_filenames, parse_keywords, workbook_bytes)


def read_text(path):
    for encoding in ('utf-8-sig', 'cp949'):
        try:
            with open(path, encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise SystemExit(f'파일을 읽을 수 없습니다 (UTF-8 / CP949 아님): {path}')


def read_filenames(source, recursive):
    if os.path.isdir(source):
        if recursive:
            return [name for _, _, files in os.walk(source) for name in sorted(files)]
        return sorted(name for name in os.listdir(source)
                      if os.path.isfile(os.path.join(source, name)))
    return parse_filenames(read_text(source))


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='키워드(한글↔영문 번역 포함)가 들어간 파일명을 골라 엑셀로 저장')
    parser.add_argument('filenames', help='파일명 목록 txt (한 줄에 하나) 또는 폴더 경로')
    parser.add_argument('keywords', help='키워드 txt (/ 또는 줄바꿈으로 구분)')
    parser.add_argument('-o', '--output', default='키워드_필터_결과.xlsx', help='저장할 엑셀 파일 경로')
    parser.add_argument('-d', '--dictionary', default=DICTIONARY_PATH, help='번역 사전 파일 경로')
    parser.add_argument('--no-translate', action='store_true', help='번역 없이 입력한 키워드만 검색')
    parser.add_argument('-r', '--recursive', action='store_true', help='폴더를 하위 폴더까지 읽기')
    args = parser.parse_args()

    filenames = read_filenames(args.filenames, args.recursive)
    keywords = parse_keywords(read_text(args.keywords))
    pairs = load_dictionary(args.dictionary)

    result = filter_filenames(filenames, keywords, pairs, translate=not args.no_translate)

    with open(args.output, 'wb') as f:
        f.write(workbook_bytes(result))

    print(f'전체 파일 {len(filenames)}개 / 키워드 {len(keywords)}개 / 사전 {len(pairs)}줄')
    print(f'키워드 포함 (제거 대상): {len(result["matched"])}개')
    print(f'나머지 파일: {len(result["unmatched"])}개')
    print(f'저장: {os.path.abspath(args.output)}')


if __name__ == '__main__':
    main()
