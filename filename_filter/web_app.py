# -*- coding: utf-8 -*-
"""
파일명 키워드 필터 - 웹 페이지

실행:
    pip install flask openpyxl
    python web_app.py
브라우저에서 http://localhost:5050 접속
"""

import os
from datetime import datetime
from urllib.parse import quote

from flask import Flask, Response, jsonify, render_template, request

from filter_core import (DICTIONARY_PATH, BASE_DIR, filter_filenames, parse_dictionary,
                         parse_keywords, workbook_bytes)

DEFAULT_KEYWORDS_PATH = os.path.join(BASE_DIR, 'keywords.txt')

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024


def read_file(path):
    if not os.path.exists(path):
        return ''
    with open(path, encoding='utf-8') as f:
        return f.read()


@app.route('/')
def index():
    return render_template('filter.html')


@app.route('/api/defaults')
def defaults():
    return jsonify({'keywords': read_file(DEFAULT_KEYWORDS_PATH).strip(),
                    'dictionary': read_file(DICTIONARY_PATH)})


@app.route('/api/dictionary', methods=['POST'])
def save_dictionary():
    text = request.get_json(force=True).get('dictionary', '')
    pairs = parse_dictionary(text)
    with open(DICTIONARY_PATH, 'w', encoding='utf-8') as f:
        f.write(text)
    return jsonify({'ok': True, 'pairs': len(pairs)})


@app.route('/api/filter', methods=['POST'])
def run_filter():
    data = request.get_json(force=True)
    filenames = [n.strip() for n in data.get('filenames', []) if n.strip()]
    keywords = parse_keywords(data.get('keywords', ''))
    pairs = parse_dictionary(data['dictionary']) if 'dictionary' in data else None
    result = filter_filenames(filenames, keywords, pairs, translate=data.get('translate', True))
    return jsonify(result)


@app.route('/api/export', methods=['POST'])
def export():
    data = request.get_json(force=True)
    result = {'matched': data.get('matched', []),
              'unmatched': data.get('unmatched', []),
              'keywords': data.get('keywords', [])}
    filename = f'키워드_필터_결과_{datetime.now():%Y%m%d_%H%M}.xlsx'
    return Response(
        workbook_bytes(result),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': "attachment; filename*=UTF-8''" + quote(filename)})


if __name__ == '__main__':
    print('파일명 키워드 필터: http://localhost:5050')
    app.run(host='127.0.0.1', port=5050, debug=False)
