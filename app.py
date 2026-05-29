# -*- coding: utf-8 -*-
"""
AV 데이터베이스 웹 플랫폼
품번기 스타일의 배우/작품 검색 사이트
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
import sys

# 부모 디렉토리의 모듈 임포트
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from av_actress_db import ACTRESS_DATABASE, format_actress_name, enrich_work_with_actress

app = Flask(__name__)
app.secret_key = 'av_platform_secret_2026'
CORS(app)

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'av_database.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db_connection():
    """데이터베이스 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """데이터베이스 초기화"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 배우 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actresses (
            id INTEGER PRIMARY KEY,
            jp_name TEXT UNIQUE NOT NULL,
            kr_name TEXT NOT NULL,
            en_name TEXT NOT NULL,
            bio TEXT,
            debut_date TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 작품 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            actress_id INTEGER,
            label TEXT,
            release_date TEXT,
            rating REAL DEFAULT 0.0,
            view_count INTEGER DEFAULT 0,
            description TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(actress_id) REFERENCES actresses(id)
        )
    ''')

    # 찜 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            work_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, work_id),
            FOREIGN KEY(work_id) REFERENCES works(id)
        )
    ''')

    # 통계 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            stat_key TEXT UNIQUE NOT NULL,
            stat_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 배너 이미지 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banners (
            id INTEGER PRIMARY KEY,
            banner_type TEXT NOT NULL,
            target_id INTEGER,
            banner_url TEXT,
            alt_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(banner_type, target_id)
        )
    ''')

    # 배우 테이블에 배너 컬럼 추가 (마이그레이션)
    try:
        cursor.execute('ALTER TABLE actresses ADD COLUMN banner_url TEXT')
    except:
        pass  # 컬럼이 이미 존재하면 무시

    # 작품 테이블에 배너 컬럼 추가 (마이그레이션)
    try:
        cursor.execute('ALTER TABLE works ADD COLUMN banner_url TEXT')
    except:
        pass  # 컬럼이 이미 존재하면 무시

    conn.commit()

    # 배우 데이터 임포트
    cursor.execute('SELECT COUNT(*) FROM actresses')
    if cursor.fetchone()[0] == 0:
        for jp_name, info in ACTRESS_DATABASE.items():
            cursor.execute('''
                INSERT INTO actresses (jp_name, kr_name, en_name, image_url)
                VALUES (?, ?, ?, ?)
            ''', (jp_name, info['kr'], info['en'], info.get('image_url')))
        conn.commit()
        print(f"✅ {len(ACTRESS_DATABASE)}명의 배우 정보가 임포트되었습니다.")

    conn.close()


def load_sample_works():
    """샘플 작품 데이터 로드 (av_ranking_history.json에서)"""
    history_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'av_ranking_history.json'
    )

    if not os.path.exists(history_path):
        return []

    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        conn = get_db_connection()
        cursor = conn.cursor()

        # 기존 작품 개수 확인
        cursor.execute('SELECT COUNT(*) FROM works')
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        # 배우 ID 목록 가져오기
        cursor.execute('SELECT id FROM actresses ORDER BY RANDOM() LIMIT 20')
        actress_ids = [row[0] for row in cursor.fetchall()]

        # 샘플 데이터 추가
        works = []
        if isinstance(data, list):
            for idx, item in enumerate(data[:20]):  # 최대 20개
                code = item.get('code', f'SAMPLE-{idx:03d}')
                title = item.get('title', f'Sample Work {idx+1}')
                rating = item.get('rating', 0.0)
                actress_id = actress_ids[idx % len(actress_ids)] if actress_ids else None

                cursor.execute('''
                    INSERT OR IGNORE INTO works
                    (code, title, label, rating, description, actress_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (code, title, '샘플', rating, '샘플 작품입니다', actress_id))
                works.append(code)

        conn.commit()
        conn.close()
        print(f"✅ {len(works)}개의 샘플 작품이 로드되었습니다. (배우 정보 포함)")
    except Exception as e:
        print(f"⚠️ 샘플 작품 로드 실패: {e}")


# ============================================================================
# 관리자 페이지 (localhost만 접근 가능)
# ============================================================================

def is_localhost():
    """localhost (127.0.0.1)에서의 요청만 허용"""
    return request.remote_addr in ['127.0.0.1', 'localhost', '::1']


@app.route('/admin')
def admin_page():
    """관리자 페이지 - 배우 이미지 URL, 작품 코드, 배너 관리"""
    if not is_localhost():
        return jsonify({'error': 'Forbidden'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 배우 목록
    cursor.execute('SELECT id, kr_name, en_name, image_url FROM actresses ORDER BY kr_name')
    actresses = [dict(row) for row in cursor.fetchall()]
    
    # 작품 목록
    cursor.execute('SELECT id, code, title FROM works ORDER BY code DESC LIMIT 50')
    works = [dict(row) for row in cursor.fetchall()]
    
    # 배너 정보
    cursor.execute('SELECT banner_type, banner_url, link_url, alt_text FROM banners WHERE banner_type IN (?, ?) ORDER BY created_at DESC', ('left', 'right'))
    banners_data = cursor.fetchall()
    left_banner = None
    right_banner = None
    for banner in banners_data:
        if dict(banner)['banner_type'] == 'left' and not left_banner:
            left_banner = dict(banner)
        elif dict(banner)['banner_type'] == 'right' and not right_banner:
            right_banner = dict(banner)
    
    conn.close()

    return render_template('admin.html', actresses=actresses, works=works, left_banner=left_banner, right_banner=right_banner)


@app.route('/api/admin/update-image', methods=['POST'])
def update_actress_image():
    """배우 이미지 URL 업데이트 (localhost만)"""
    if not is_localhost():
        return jsonify({'error': 'Forbidden'}), 403

    data = request.json
    actress_id = data.get('actress_id')
    image_url = data.get('image_url')

    if not actress_id or not image_url:
        return jsonify({'error': 'Missing data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE actresses SET image_url = ? WHERE id = ?', (image_url, actress_id))
        conn.commit()

        # 업데이트 확인
        cursor.execute('SELECT image_url FROM actresses WHERE id = ?', (actress_id,))
        updated = cursor.fetchone()
        conn.close()

        if updated and updated[0] == image_url:
            return jsonify({'success': True, 'message': '저장되었습니다'})
        else:
            return jsonify({'success': False, 'error': '저장 실패'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/update-code', methods=['POST'])
def update_work_code():
    """작품 코드(품번) 업데이트 (localhost만) - 하위호환성"""
    if not is_localhost():
        return jsonify({'error': 'Forbidden'}), 403

    data = request.json
    work_id = data.get('work_id')
    code = data.get('code', '').strip().upper()

    if not work_id or not code:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 중복 확인
        cursor.execute('SELECT id FROM works WHERE code = ? AND id != ?', (code, work_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': '이미 존재하는 품번입니다'}), 400
        
        cursor.execute('UPDATE works SET code = ? WHERE id = ?', (code, work_id))
        conn.commit()

        # 업데이트 확인
        cursor.execute('SELECT code FROM works WHERE id = ?', (work_id,))
        updated = cursor.fetchone()
        conn.close()

        if updated and updated[0] == code:
            return jsonify({'success': True, 'message': '저장되었습니다'})
        else:
            return jsonify({'success': False, 'error': '저장 실패'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/update-work', methods=['POST'])
def update_work_info():
    """작품 정보 업데이트 (품번 + 이미지) (localhost만)"""
    if not is_localhost():
        return jsonify({'error': 'Forbidden'}), 403

    data = request.json
    work_id = data.get('work_id')
    code = data.get('code')
    image_url = data.get('image_url')

    if not work_id or (not code and not image_url):
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 품번 업데이트 (코드가 있으면)
        if code:
            code = code.strip().upper()
            # 중복 확인
            cursor.execute('SELECT id FROM works WHERE code = ? AND id != ?', (code, work_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'error': '이미 존재하는 품번입니다'}), 400
            
            cursor.execute('UPDATE works SET code = ? WHERE id = ?', (code, work_id))
        
        # 이미지 업데이트 (이미지가 있으면)
        if image_url:
            image_url = image_url.strip()
            cursor.execute('UPDATE works SET image_url = ? WHERE id = ?', (image_url, work_id))
        
        conn.commit()

        # 업데이트 확인
        if code:
            cursor.execute('SELECT code, image_url FROM works WHERE id = ?', (work_id,))
            updated = cursor.fetchone()
            conn.close()
            
            if updated:
                return jsonify({'success': True, 'message': '저장되었습니다'})
        else:
            cursor.execute('SELECT image_url FROM works WHERE id = ?', (work_id,))
            updated = cursor.fetchone()
            conn.close()
            
            if updated and updated[0] == image_url:
                return jsonify({'success': True, 'message': '저장되었습니다'})
        
        return jsonify({'success': False, 'error': '저장 실패'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/update-banner', methods=['POST'])
def update_banner():
    """배너 업데이트 (localhost만)"""
    if not is_localhost():
        return jsonify({'error': 'Forbidden'}), 403

    data = request.json
    banner_type = data.get('banner_type')  # 'left' or 'right'
    banner_url = data.get('banner_url')
    link_url = data.get('link_url')
    alt_text = data.get('alt_text', '')

    if not banner_type or not banner_url:
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    if banner_type not in ['left', 'right']:
        return jsonify({'success': False, 'error': 'Invalid banner type'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 기존 배너 삭제 후 새로 추가 (덮어쓰기)
        cursor.execute('DELETE FROM banners WHERE banner_type = ?', (banner_type,))
        
        cursor.execute('''
            INSERT INTO banners (banner_type, banner_url, link_url, alt_text)
            VALUES (?, ?, ?, ?)
        ''', (banner_type, banner_url, link_url, alt_text))
        
        conn.commit()
        
        # 저장 확인
        cursor.execute('SELECT banner_url FROM banners WHERE banner_type = ?', (banner_type,))
        updated = cursor.fetchone()
        conn.close()

        if updated and updated[0] == banner_url:
            return jsonify({'success': True, 'message': '저장되었습니다'})
        else:
            return jsonify({'success': False, 'error': '저장 실패'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API 엔드포인트
# ============================================================================

@app.route('/')
def index():
    """메인 페이지"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 통계 정보
    cursor.execute('SELECT COUNT(*) FROM actresses')
    actress_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM works')
    work_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM works WHERE rating > 0')
    rated_count = cursor.fetchone()[0]

    # 최신 추가된 작품
    cursor.execute('''
        SELECT w.id, w.code, w.title, w.rating, w.created_at, a.kr_name
        FROM works w
        LEFT JOIN actresses a ON w.actress_id = a.id
        ORDER BY w.created_at DESC
        LIMIT 8
    ''')
    recent_works = [dict(row) for row in cursor.fetchall()]

    # 모든 배우 목록 (초기 로드)
    cursor.execute('''
        SELECT id, jp_name, kr_name, en_name, image_url
        FROM actresses
        ORDER BY kr_name ASC
    ''')
    all_actresses = [dict(row) for row in cursor.fetchall()]

    # 최신 추가 작품 (작품 검색용)
    cursor.execute('''
        SELECT w.id, w.code, w.title, w.rating, a.kr_name, w.label
        FROM works w
        LEFT JOIN actresses a ON w.actress_id = a.id
        ORDER BY w.created_at DESC
        LIMIT 12
    ''')
    latest_works = [dict(row) for row in cursor.fetchall()]

    # 배너 데이터
    cursor.execute('SELECT banner_url, link_url, alt_text FROM banners WHERE banner_type = ? ORDER BY created_at DESC LIMIT 1', ('left',))
    left_banner_row = cursor.fetchone()
    left_banner = dict(left_banner_row) if left_banner_row else None

    cursor.execute('SELECT banner_url, link_url, alt_text FROM banners WHERE banner_type = ? ORDER BY created_at DESC LIMIT 1', ('right',))
    right_banner_row = cursor.fetchone()
    right_banner = dict(right_banner_row) if right_banner_row else None

    conn.close()

    return render_template('index.html',
                         actress_count=actress_count,
                         work_count=work_count,
                         rated_count=rated_count,
                         recent_works=recent_works,
                         all_actresses=all_actresses,
                         latest_works=latest_works,
                         left_banner=left_banner,
                         right_banner=right_banner)


@app.route('/search')
def search_page():
    """검색 결과 페이지"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    return render_template('search_results.html', query=query, search_type=search_type)


@app.route('/api/search', methods=['GET'])
def search():
    """검색 API"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # all, actress, work
    page = int(request.args.get('page', 1))
    per_page = 12
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor()

    results = {'actresses': [], 'works': [], 'total': 0}

    if not query:
        return jsonify(results)

    # 배우 검색
    if search_type in ['all', 'actress']:
        cursor.execute('''
            SELECT id, jp_name, kr_name, en_name, image_url
            FROM actresses
            WHERE kr_name LIKE ? OR en_name LIKE ? OR jp_name LIKE ?
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', 20))
        results['actresses'] = [dict(row) for row in cursor.fetchall()]

    # 작품 검색
    if search_type in ['all', 'work']:
        cursor.execute('''
            SELECT w.id, w.code, w.title, w.rating, a.kr_name, w.label
            FROM works w
            LEFT JOIN actresses a ON w.actress_id = a.id
            WHERE w.code LIKE ? OR w.title LIKE ?
            ORDER BY w.rating DESC
            LIMIT ? OFFSET ?
        ''', (f'%{query}%', f'%{query}%', per_page, offset))
        results['works'] = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT COUNT(*) FROM works
            WHERE code LIKE ? OR title LIKE ?
        ''', (f'%{query}%', f'%{query}%'))
        results['total'] = cursor.fetchone()[0]

    conn.close()
    return jsonify(results)


@app.route('/actress/<int:actress_id>')
def actress_detail(actress_id):
    """배우 상세 페이지"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, jp_name, kr_name, en_name, image_url FROM actresses WHERE id = ?', (actress_id,))
    actress = cursor.fetchone()

    if not actress:
        conn.close()
        return render_template('404.html'), 404

    actress = dict(actress)

    # 배우의 작품 목록
    cursor.execute('''
        SELECT id, code, title, rating, label, release_date
        FROM works
        WHERE actress_id = ?
        ORDER BY release_date DESC
    ''', (actress_id,))
    works = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return render_template('actress_detail.html', actress=actress, works=works)


@app.route('/work/<int:work_id>')
def work_detail(work_id):
    """작품 상세 페이지"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT w.id, w.code, w.title, w.label, w.rating,
               w.description, w.view_count, w.release_date,
               a.id as actress_id, a.kr_name, a.en_name, a.image_url
        FROM works w
        LEFT JOIN actresses a ON w.actress_id = a.id
        WHERE w.id = ?
    ''', (work_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return render_template('404.html'), 404

    work = dict(row)
    work['actress_image'] = work.get('image_url')

    # 조회수 증가
    cursor.execute('UPDATE works SET view_count = view_count + 1 WHERE id = ?', (work_id,))
    conn.commit()
    conn.close()

    return render_template('work_detail.html', work=work)


@app.route('/api/works/<int:work_id>')
def get_work_detail(work_id):
    """작품 상세 정보 API"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT w.id, w.code, w.title, w.label, w.rating,
               w.description, w.view_count, w.release_date, a.kr_name
        FROM works w
        LEFT JOIN actresses a ON w.actress_id = a.id
        WHERE w.id = ?
    ''', (work_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404

    work = dict(row)

    # 조회수 증가
    cursor.execute('UPDATE works SET view_count = view_count + 1 WHERE id = ?', (work_id,))
    conn.commit()
    conn.close()

    return jsonify(work)


@app.route('/api/actresses')
def list_actresses():
    """배우 목록"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, jp_name, kr_name, en_name, image_url FROM actresses ORDER BY kr_name')
    actresses = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify({'actresses': actresses})


@app.route('/api/actresses/<int:actress_id>/works')
def get_actress_works(actress_id):
    """배우의 모든 작품"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, code, title, rating, label
        FROM works
        WHERE actress_id = ?
        ORDER BY rating DESC
    ''', (actress_id,))

    works = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(works)


@app.route('/api/favorites', methods=['GET', 'POST', 'DELETE'])
def manage_favorites():
    """찜 목록 관리"""
    session_id = session.get('session_id', request.remote_addr)
    session['session_id'] = session_id

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('''
            SELECT w.id, w.code, w.title, w.rating, a.kr_name
            FROM favorites f
            JOIN works w ON f.work_id = w.id
            LEFT JOIN actresses a ON w.actress_id = a.id
            WHERE f.session_id = ?
            ORDER BY f.created_at DESC
        ''', (session_id,))
        favorites = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(favorites)

    elif request.method == 'POST':
        work_id = request.json.get('work_id')
        try:
            cursor.execute('''
                INSERT INTO favorites (session_id, work_id)
                VALUES (?, ?)
            ''', (session_id, work_id))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Already in favorites'}), 400

    elif request.method == 'DELETE':
        work_id = request.json.get('work_id')
        cursor.execute('''
            DELETE FROM favorites
            WHERE session_id = ? AND work_id = ?
        ''', (session_id, work_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})


@app.route('/api/stats')
def get_stats():
    """플랫폼 통계"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM actresses')
    actress_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM works')
    work_count = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(rating) FROM works WHERE rating > 0')
    avg_rating = cursor.fetchone()[0] or 0.0

    cursor.execute('SELECT SUM(view_count) FROM works')
    total_views = cursor.fetchone()[0] or 0

    conn.close()

    return jsonify({
        'actresses': actress_count,
        'works': work_count,
        'avg_rating': round(avg_rating, 1),
        'total_views': total_views
    })


@app.route('/api/actresses/list')
def list_actresses_by_ids():
    """특정 ID의 배우 목록"""
    ids = request.args.get('ids', '').split(',')
    ids = [int(id) for id in ids if id.strip().isdigit()]

    if not ids:
        return jsonify({'actresses': []})

    conn = get_db_connection()
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(ids))
    cursor.execute(f'SELECT id, jp_name, kr_name, en_name, image_url FROM actresses WHERE id IN ({placeholders})', ids)
    actresses = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify({'actresses': actresses})


@app.route('/api/works/by-label/<label>')
def get_works_by_label(label):
    """레이블별 작품"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT w.id, w.code, w.title, w.rating, a.kr_name
        FROM works w
        LEFT JOIN actresses a ON w.actress_id = a.id
        WHERE w.label = ?
        ORDER BY w.rating DESC
        LIMIT 12
    ''', (label,))

    works = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(works)


@app.route('/api/actresses/<int:actress_id>/stats')
def get_actress_stats(actress_id):
    """배우 통계"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT kr_name FROM actresses WHERE id = ?', (actress_id,))
    actress = cursor.fetchone()
    if not actress:
        conn.close()
        return jsonify({'error': 'Not found'}), 404

    cursor.execute('''
        SELECT COUNT(*) as count, AVG(rating) as avg_rating, SUM(view_count) as total_views
        FROM works WHERE actress_id = ?
    ''', (actress_id,))

    stats = dict(cursor.fetchone())
    conn.close()

    return jsonify({
        'actress_name': actress['kr_name'],
        'work_count': stats['count'] or 0,
        'avg_rating': round(stats['avg_rating'] or 0.0, 1),
        'total_views': stats['total_views'] or 0
    })


# ============================================================================
# 에러 핸들러
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    # 데이터베이스 초기화
    init_db()
    load_sample_works()

    print("🚀 AV 웹 플랫폼 시작...")
    print("📍 http://localhost:5000")

    app.run(debug=True, host='0.0.0.0', port=5000)
