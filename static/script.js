// 다크 모드 토글
function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
}

// 저장된 테마 로드
function loadTheme() {
    const theme = localStorage.getItem('theme') || 'light';
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    }
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    loadTheme();

    // 테마 토글 버튼
    document.querySelector('.theme-toggle').addEventListener('click', toggleTheme);

    // 모달 닫기
    document.addEventListener('click', function(e) {
        const modal = document.getElementById('searchModal');
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    });

    const modalClose = document.querySelector('.modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', function() {
            document.getElementById('searchModal').classList.remove('show');
        });
    }

    // ESC 키로 모달 닫기
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.getElementById('searchModal').classList.remove('show');
        }
    });
});

// 페이지 스크롤 자동 위치 조정
window.addEventListener('load', function() {
    const hash = window.location.hash;
    if (hash) {
        const element = document.querySelector(hash);
        if (element) {
            setTimeout(() => {
                element.scrollIntoView({ behavior: 'smooth' });
            }, 100);
        }
    }
});
