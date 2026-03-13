# 20000 — 모바일/태블릿에서 플레이하기

이 프로젝트는 **PC**와 **휴대폰·태블릿** 모두에서 플레이할 수 있도록 터치 조작을 지원합니다.

## 조작 방법

- **PC**: 방향키(←→↑↓) + 스페이스(발사). 게임 오버/클리어 시 R(재시작), M(메뉴), ESC(종료).
- **모바일/태블릿**: 화면 하단의 **가상 버튼** 사용.
  - 왼쪽: L(좌), R(우), U(상), D(하)
  - 오른쪽: FIRE(발사)
  - 게임 오버/클리어 시 화면의 "Restart", "Main Menu" 영역 터치

## 필요한 파일 (같은 폴더에 두기)

- `20000.py`
- `기본우주선.png`, `업그레이드우주선.png`, `적 우주선.png`
- `브론즈보스.png`, `실버보스.png`, `골드보스.png`, `플래티넘보스.png`
- `배경음.mp3`, `폭발.mp3`

## Android (휴대폰/태블릿)

### 방법 1: Pydroid 3 (가장 간단)

1. Play 스토어에서 **Pydroid 3** 설치.
2. Pydroid에서 **pip**로 `pygame` 설치: 메뉴 → Pip → `pygame` 설치.
3. 위 필요한 파일들이 들어 있는 폴더를 기기에 복사(USB 또는 클라우드).
4. Pydroid에서 `20000.py` 열고 **Run** 실행.
5. 화면 하단 버튼으로 이동·발사.

### 방법 2: APK로 빌드 (Buildozer)

PC에서 Android APK를 만들려면 **Buildozer**와 **python-for-android**를 사용합니다.

- [Buildozer 문서](https://buildozer.readthedocs.io/) 참고.
- `buildozer.spec`에서 `source.include_exts`에 `.png`, `.mp3` 등 에셋 확장자 추가.
- 에셋 파일을 프로젝트 폴더에 두고 `buildozer android debug` 실행.

## iOS / 브라우저

- **iOS**: Pygame을 직접 실행하는 공식 앱은 제한적입니다. PC에서 빌드한 뒤 실기기에 올리는 방식은 별도 도구가 필요합니다.
- **브라우저**: [Pygbag](https://pygame-web.github.io/)으로 웹에서 실행할 수 있으나, 이 프로젝트는 현재 Pygbag용 비동기 루프로 수정되어 있지 않습니다. 브라우저 지원이 필요하면 Pygbag 문서를 참고해 `async` 진입점을 추가해야 합니다.

## 현재 저장된 상태

- 제목: **20000**
- 등급: Bronze1 ~ Platinum2 (클리어 시 게임 클리어 화면, 등급은 Platinum2 유지)
- 5% 파란 회복탄(체력 30), 플래티넘 보스 격파 시 게임 클리어
- 누적 등급·보스 처치 기록은 `우주선_등급저장.json`에 저장
