#!/usr/bin/env python3
"""Build editable Korean slides using system Python + LibreOffice UNO."""

import argparse
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException


ROOT = Path(__file__).resolve().parents[1]
NAVY, INK, PAPER = 0x102532, 0x183340, 0xF4F1E9
TEAL, ORANGE, MUTED = 0x75D5C5, 0xFFB66B, 0xABC0CB
FONT = "Noto Sans CJK KR"
STAGES = ["전체 지도", "CPU·메모리", "어셈블리", "부팅·보호", "init·셸", "관찰·정리"]


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


class Deck:
    def __init__(self, doc):
        self.doc = doc
        self.pages = doc.getDrawPages()
        self.count = 0
        first = self.pages.getByIndex(0)
        while first.getCount():
            first.remove(first.getByIndex(0))

    def shape(self, page, x, y, w, h, fill=None):
        shape = self.doc.createInstance("com.sun.star.drawing.RectangleShape")
        shape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", x, y))
        shape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", w, h))
        page.add(shape)
        shape.LineStyle = uno.Enum("com.sun.star.drawing.LineStyle", "NONE")
        shape.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "SOLID")
        shape.FillColor = fill if fill is not None else NAVY
        return shape

    def text(self, page, x, y, w, h, text, size=20, color=PAPER, bold=False):
        shape = self.doc.createInstance("com.sun.star.drawing.TextShape")
        shape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", x, y))
        shape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", w, h))
        page.add(shape)
        shape.TextAutoGrowHeight = False
        shape.TextAutoGrowWidth = False
        shape.TextLeftDistance = shape.TextRightDistance = 0
        shape.TextUpperDistance = shape.TextLowerDistance = 0
        shape.setString(text)
        cursor = shape.getText().createTextCursor()
        cursor.gotoStart(False)
        cursor.gotoEnd(True)
        cursor.CharFontName = cursor.CharFontNameAsian = FONT
        cursor.CharHeight = cursor.CharHeightAsian = float(size)
        cursor.CharColor = color
        cursor.CharWeight = cursor.CharWeightAsian = 150.0 if bold else 100.0
        return shape

    def slide(self, title, stage, note):
        page = (self.pages.getByIndex(0) if self.count == 0
                else self.pages.insertNewByIndex(self.pages.getCount()))
        self.count += 1
        page.Width, page.Height = 33867, 19050
        bg = self.doc.createInstance("com.sun.star.drawing.Background")
        bg.FillColor = NAVY
        page.Background = bg
        number = self.pages.getCount()
        page.Name = f"{number:02d} {title}"
        self.text(page, 1100, 400, 30000, 550,
                  "LINUX 0.11 / SOURCE WALKTHROUGH                         01  소스 지도와 전체 실행 흐름", 11, TEAL)
        self.text(page, 1100, 1200, 31400, 1450, title, 29, PAPER, True)
        for i, label in enumerate(STAGES):
            x = 1100 + i * 5300
            self.shape(page, x, 3000, 5000, 850, TEAL if i == stage else 0x203D4B)
            self.text(page, x + 200, 3120, 4600, 600, f"{i+1:02d}  {label}",
                      13, INK if i == stage else MUTED, i == stage)
        self.shape(page, 1100, 17750, 31500, 35, 0x36525F)
        self.text(page, 1100, 18000, 29500, 650, note, 10, MUTED)
        self.text(page, 31400, 17950, 1200, 650, f"{number:02d}", 14, TEAL)
        return page

    def cards(self, page, cards, y=4700, h=8500):
        gap, total = 600, 31500
        width = (total - gap * (len(cards) - 1)) // len(cards)
        for i, (title, body) in enumerate(cards):
            x = 1100 + i * (width + gap)
            self.shape(page, x, y, width, h, PAPER)
            self.shape(page, x, y, width, 150, TEAL if i % 2 == 0 else ORANGE)
            self.text(page, x + 550, y + 650, width - 1100, 1600, title, 21, INK, True)
            self.text(page, x + 550, y + 2600, width - 1100, h - 2800, body, 18, INK)

    def banner(self, page, text, y=15000):
        self.text(page, 1400, y, 30500, 2000, text, 20, ORANGE, True)

    def flow(self, page, items, y=5300, h=3000):
        n = len(items)
        w = (31500 - (n - 1) * 1100) // n
        for i, (title, body) in enumerate(items):
            x = 1100 + i * (w + 1100)
            self.shape(page, x, y, w, h, PAPER)
            self.text(page, x + 300, y + 350, w - 600, 950, title, 19, INK, True)
            self.text(page, x + 300, y + 1400, w - 600, h - 1450, body, 15, INK)
            if i < n - 1:
                self.text(page, x + w + 150, y + 800, 850, 1000, ">", 28, TEAL, True)

    def code(self, page, path, start, end, explanation):
        lines = (ROOT / path).read_text().splitlines()
        displayed = []
        for i in range(start, end + 1):
            line = lines[i-1].expandtabs(4)
            line = line.split("!" if path.endswith(".s") else "/*", 1)[0].rstrip()
            displayed.append(f"{i:3}  {line}")
        snippet = "\n".join(displayed)
        self.shape(page, 1100, 4600, 19700, 11600, 0x071A24)
        self.text(page, 1550, 4900, 18800, 650,
                  f"{path}:{start}-{end}  / 인라인 주석 생략", 12, TEAL)
        code_shape = self.text(page, 1550, 5900, 18800, 9800, snippet, 14)
        cursor = code_shape.getText().createTextCursor()
        cursor.gotoEnd(True)
        cursor.CharFontName = "DejaVu Sans Mono"
        self.text(page, 22000, 5000, 10000, 11000, explanation, 20)


def populate(d):
    p = d.slide("전원 투입에서 셸까지, 코드로 연결하기", 0, "강사 시연 + 소스 해설 / 원본 src · 실행 수정본 lab")
    d.text(p, 1400, 5100, 30000, 2800, "셸 프롬프트 하나가 나타나기까지\n커널은 무엇을 준비해야 할까?", 34, PAPER, True)
    d.flow(p, [("BOOT", "코드 적재"), ("KERNEL", "실행 기반 준비"), ("INIT", "사용자 실행 준비"), ("SHELL", "명령 해석과 실행")], 10000)
    d.banner(p, "CPU·보호 모드·어셈블리를 몰라도 시작한다. C의 함수·변수 개념만 사용한다.")

    p = d.slide("16회 과정에서 오늘의 위치", 0, "1회차는 전체 지도 / 15~16회는 별도 현대 Linux VM 사용")
    d.cards(p, [("01–04  진입 경로", "[현재] 소스 지도\nx86 기초\n부팅과 초기화\n인터럽트·시스템 콜"), ("05–10  실행과 메모리", "스케줄링과 fork\n주소 변환과 COW\nexec\n종료·대기·시그널"), ("11–16  I/O와 확장", "파일·버퍼·터미널\n전체 흐름 통합\n현대 커널 모듈\n0.11 / 현대 스케줄러")])
    d.banner(p, "매 회차: 현재 위치 지도 + 상태 변화도 + 관련 모드·선택지 전체 비교")

    p = d.slide("컴퓨터의 네 요소: 누가 계산하고 어디에 저장할까?", 1, "CPU=중앙 처리 장치 / x86=명령 체계 계열, 80386=이번 대상 CPU / 캐시·배선은 생략")
    d.cards(p, [("CPU: 명령 실행", "명령을 읽고 계산한다.\n레지스터: CPU 안의 작은 저장소\n\n메모리에 있는 코드와\n데이터를 사용한다."), ("메모리와 디스크", "RAM: 실행 중 코드·데이터\n디스크: 파일의 지속 저장\n\n디스크의 프로그램을\n메모리로 읽어 실행한다."), ("입출력 장치", "키보드: 입력\n화면: 출력\n디스크 제어기: 저장 장치 연결\n\n커널이 장치 접근을 관리한다.")])
    d.banner(p, "CPU는 C 소스 파일을 직접 읽지 않는다. 메모리의 기계어 명령을 실행한다.")

    p = d.slide("숫자 표기부터: bit, byte, 16진수", 1, "0x와 #, $는 서로 다른 역할 / 0x는 숫자 진법을 나타내는 표기")
    d.cards(p, [("bit와 byte", "bit: 0 또는 1\nbyte: 8 bits\n\n16비트: 2 bytes\n32비트: 4 bytes"), ("16진수 읽기", "한 자리: 0~9, A~F\n0x10 = 십진수 16\n0x17 = 십진수 23\n\n주소·비트 패턴에 편리하다."), ("제어 비트", "여러 비트 중 하나가\n기능의 켜짐·꺼짐을 표현한다.\n\n예: PE는 보호 기능\nPG는 페이징 기능")])
    d.banner(p, "32비트라는 말은 모든 명령이 4바이트이거나 RAM이 4GB라는 뜻이 아니다.")

    p = d.slide("메모리 주소와 값은 서로 다른 것이다", 1, "단순 byte 주소 예제 / 주소는 위치, 그 위치에 든 내용은 값")
    d.cards(p, [("주소: 저장 위치", "주소 0x1000: 값 7\n주소 0x1001: 값 9\n\n포인터는 위치를 가리킨다.\n주소 자체와 저장된 값을 구분."), ("읽기와 쓰기", "읽기: 해당 위치의 값을 가져옴\n쓰기: 해당 위치의 값을 바꿈\n\n메모리 쓰기는 곧\n디스크 파일 저장이 아니다.")])
    d.flow(p, [("변경 전", "[0x1000] = 7"), ("쓰기 동작", "주소 0x1000에 12 저장"), ("변경 후", "[0x1000] = 12")], y=13600, h=2900)

    p = d.slide("레지스터: CPU가 당장 사용하는 작은 저장소", 1, "x86의 이번 수업용 최소 집합 / 레지스터 전체 목록을 암기하지 않는다")
    d.cards(p, [("EAX / AX", "계산·임시 값 등에 사용\nEAX: 32비트\nAX: EAX의 하위 16비트\n\nAX 변경은 EAX 일부 변경"), ("EIP / ESP", "EIP: 다음 명령 위치의 기준\nCS와 함께 실행 위치 결정\n\nESP: 스택 꼭대기 위치\nSS와 함께 스택 위치 결정"), ("EFLAGS / 제어", "EFLAGS: 상태·제어 비트\nIF: 일반 IRQ 허용 여부\n\nCR0: PE·PG 등 CPU 설정\nCR3: 페이지 변환표 위치")])
    d.banner(p, "C의 변수와 레지스터는 1:1 대응이 아니다. 컴파일러가 배치를 결정한다.")

    p = d.slide("CPU의 반복 동작: 읽기 → 해석 → 실행", 1, "실제 CPU 내부 파이프라인을 생략한 순차 실행 모델")
    d.flow(p, [("명령 읽기", "현재 실행 위치의\n기계어를 가져온다."), ("명령 해석", "복사·계산·분기 등\n수행할 일을 판단한다."), ("명령 실행", "레지스터·메모리 변경\n다음 실행 위치 결정")], h=4000)
    d.text(p, 1400, 10500, 30500, 3300, "보통은 다음 명령으로 진행한다.\njump는 다른 위치로 이동하고, call은 돌아올 위치를 남긴다.\nCPU는 이 과정을 반복한다. 운영체제도 결국 같은 CPU 명령으로 실행된다.", 22)
    d.banner(p, "상태 = 현재 레지스터 값 + 관련 메모리 내용 + CPU 제어 설정")

    p = d.slide("C, 어셈블리, 기계어는 어떻게 연결될까?", 2, "개념적인 빌드 경로 / 실제 프로젝트의 도구와 세부 단계는 별도 확인")
    d.flow(p, [("C 소스", "사람이 쓰는 함수·변수\n컴파일러가 번역"), ("어셈블리", "CPU 명령의 텍스트 표기\n어셈블러가 번역"), ("기계어·실행 이미지", "숫자 바이트의 명령\n링크 후 적재·실행")], h=4200)
    d.text(p, 1400, 10600, 30500, 3200, ".c: C 소스, .s: 어셈블리 소스, .o: 중간 목적 파일\n부팅 코드는 C 실행에 필요한 스택·실행 환경을 먼저 준비한다.\n따라서 일부 시작 코드는 어셈블리로 직접 작성되어 있다.", 22)
    d.banner(p, "어셈블리는 다른 CPU가 아니라, CPU 명령을 사람이 읽기 위한 표기다.")

    p = d.slide("어셈블리 읽기: 명령 이름과 두 피연산자", 2, "두 표기는 같은 복사 동작 / 예시는 설명용이며 원본 발췌가 아니다")
    d.cards(p, [("setup.s의 as86 표기", "mov ax,#0x0001\n\nmov: 값을 복사\nax: 목적 레지스터\n#0x0001: 즉시 값 1\n\n순서: 목적지, 원본"), ("head.s의 GNU AT&T", "movl $0x00000001,%eax\n\nmovl: 32비트 값 복사\n$1: 즉시 값 1\n%eax: 레지스터 이름\n\n순서: 원본, 목적지")], h=9500)
    d.banner(p, "주의: 피연산자 순서가 반대다. 파일의 문법을 먼저 확인한다.", y=15100)

    p = d.slide("명령을 한 줄 실행하면 어떤 값이 바뀔까?", 2, "설명용 AT&T 예제 / 이 예제의 명령 실행은 QEMU에서 측정한 결과가 아니다")
    d.flow(p, [("시작", "EAX 값은 미정"), ("movl $1,%eax", "EAX = 1\n메모리 쓰기 없음"), ("addl $2,%eax", "EAX = 3\n산술 상태 비트도 변경")], h=4200)
    d.text(p, 1400, 10800, 30500, 3000, "mov는 원본을 지우는 이동이 아니라 값을 복사하는 동작이다.\n$1은 숫자 1이고, 메모리 주소 1에서 읽으라는 뜻이 아니다.\n명령마다 바뀌는 값과 그대로인 값을 따로 짚는다.", 22)
    d.banner(p, "확인 질문: movl $1,%eax 뒤 EAX는 주소일까, 숫자 1일까?")

    p = d.slide("스택: 마지막에 넣은 것을 먼저 꺼낸다", 2, "32비트 push/pop 예제 / x86 스택은 낮은 주소 방향으로 자란다")
    d.flow(p, [("시작", "ESP = 0x1000"), ("pushl $7", "ESP = 0x0FFC\n[0x0FFC] = 7"), ("popl %eax", "EAX = 7\nESP = 0x1000")], h=4200)
    d.text(p, 1400, 10800, 30500, 3000, "push: 스택 위치를 낮추고 값을 저장한다. pop: 값을 읽고 위치를 높인다.\ncall: 돌아올 명령 위치를 스택에 남기고 이동한다. ret: 그 위치로 돌아간다.\n이후 iret는 실행 위치뿐 아니라 권한 복귀에 필요한 상태도 복원한다.", 21)
    d.banner(p, "pop은 메모리의 바이트를 반드시 0으로 지우는 동작은 아니다.")

    p = d.slide("왜 커널과 사용자 프로그램을 구분할까?", 3, "보호의 목적을 먼저 이해한 뒤 x86 구현 용어를 도입한다")
    d.cards(p, [("사용자 프로그램", "셸·편집기·일반 명령\n실수나 오류가 생길 수 있다.\n\n다른 프로그램의 메모리나\n장치를 마음대로 바꾸면 위험"), ("커널", "메모리·CPU·장치를 관리\n요청을 검사하고 처리한다.\n\n사용자는 시스템 콜이라는\n정해진 경로로 서비스를 요청")])
    d.banner(p, "역할 분담만으로는 부족하다. CPU가 접근 권한을 검사해야 한다.")

    p = d.slide("보호 모드: CPU가 접근 규칙을 검사하는 환경", 3, "보호 모드와 사용자 권한은 다른 분류 / 보호 모드가 모든 오류를 자동 방지하지는 않음")
    d.cards(p, [("실주소 모드", "초기 PC와의 호환 환경\n세그먼트×16 + 오프셋으로\n주소를 만드는 기본 모델\n\n보호 모드식 권한 분리 없음"), ("보호 모드", "세그먼트 설명표 참조\n주소 범위·접근 권한 검사\n권한 수준으로 동작 구분\n\n페이징은 별도로 켤 수 있음")])
    d.banner(p, "Linux 0.11의 커널과 사용자 프로그램은 둘 다 보호 모드에서 실행한다.")

    p = d.slide("세그먼트와 GDT: 번호로 실행 규칙을 찾는다", 3, "GDT = Global Descriptor Table / 사용자 영역의 LDT 상세는 2회차에서 설명")
    d.flow(p, [("CS의 선택자", "예: 8 = 0x0008\n메모리 주소 자체가 아님"), ("GDT의 항목", "시작 주소·범위·권한\n코드/데이터 등 기록"), ("주소와 검사", "시작 주소 + 오프셋\n범위·권한을 검사")], h=4300)
    d.text(p, 1400, 10900, 30500, 3000, "CS: 코드 세그먼트 선택자, DS: 데이터, SS: 스택에 사용한다.\nGDT는 CPU가 규칙을 찾는 표, IDT는 인터럽트·예외 진입 정보를 찾는 표다.\n선택자의 비트 배치와 설명표 형식은 오늘 암기하지 않는다.", 21)
    d.banner(p, "보호 모드에서 segment×16을 그대로 사용하는 것으로 설명하지 않는다.")

    p = d.slide("페이징: CPU가 주소를 한 번 더 변환한다", 3, "설명용 매핑 예제 / 실제 0.11 초기 매핑과 구분한다")
    d.flow(p, [("프로그램의 위치", "세그먼트 규칙 적용\n선형 주소 0x2000"), ("페이지 변환표", "0x2000을 포함한 페이지\n→ 물리 페이지 0x9000"), ("실제 RAM 위치", "물리 주소 0x9000\n이 위치의 데이터 사용")], h=4300)
    d.text(p, 1400, 10900, 30500, 3000, "페이징 꺼짐: 선형 주소를 페이지 표로 변환하지 않는다.\n페이징 켜짐: 페이지 디렉터리·테이블을 거쳐 물리 주소를 구한다.\n0.11의 초기 설정은 0~16 MiB의 선형·물리 주소를 같게 매핑한다.", 21)
    d.banner(p, "CR3는 변환표의 시작 위치, CR0.PG는 변환 기능을 켜는 비트다.")

    p = d.slide("CPU가 실행을 잠시 바꾸는 세 가지 이유", 3, "이번 경로에서 구분할 사건 / IDT의 구체 형식과 예외 분류는 4회차")
    d.cards(p, [("하드웨어 인터럽트", "타이머·키보드 등 장치 신호\n현재 명령 흐름과 별개로 발생\n\nIRQ: 장치의 인터럽트 요청\nIF로 일반 IRQ 허용 제어"), ("예외", "명령 실행 중 CPU가 감지\n예: 0으로 나눔·페이지 폴트\n\n페이지 폴트는\n항상 프로그램 버그는 아님"), ("시스템 콜", "프로그램이 의도적으로 요청\n예: 파일 읽기·프로세스 생성\n\n0.11에서는 int $0x80 사용\n정해진 커널 경로로 진입")])
    d.banner(p, "IF=0이어도 예외와 NMI(마스크 불가능 인터럽트)까지 모두 차단되지는 않는다.")

    p = d.slide("실행 문맥과 iret: 돌아갈 위치와 권한을 복원한다", 3, "iret = interrupt return / 초기 사용자 문맥 진입에도 복원 형식을 활용")
    d.flow(p, [("복원할 정보 준비", "EIP·CS: 코드 위치\nEFLAGS: 상태 비트"), ("권한도 바뀐다면", "ESP·SS: 사용자 스택\n추가 정보도 준비"), ("iret 실행", "저장된 실행 상태 복원\n해당 권한·위치로 진행")], h=4300)
    d.text(p, 1400, 10900, 30500, 3000, "일반 ret와 달리 iret는 실행 상태와 권한 복귀 규칙을 처리한다.\n처음 사용자 영역으로 갈 때도 '복귀할 상태'를 미리 만들어 사용할 수 있다.\n범용 레지스터 모두를 iret 한 명령이 자동 복원하는 것은 아니다.", 21)
    d.banner(p, "문맥은 소스 파일 이름이 아니라, CPU가 지금 실행하는 데 필요한 상태다.")

    p = d.slide("약어 해독표: 비트와 권한을 서로 섞지 않는다", 3, "이후 원본 코드 옆에 다시 찾아볼 참조표 / 0과 1은 각 비트의 값")
    d.cards(p, [("CR0.PE / CR0.PG", "CR0: CPU 제어 레지스터\nPE=0: 실주소 모드\nPE=1: 보호 환경\n\nPG=0: 페이징 안 함\nPG=1: 페이징 사용"), ("CPL / EFLAGS.IF", "CPL: 현재 권한 수준 0~3\n0: 커널 / 3: 사용자 주 경로\n\nIF=0: 일반 IRQ 억제\nIF=1: 일반 IRQ 허용\nNMI·예외는 별도")], h=9500)
    d.banner(p, "보호 모드 진입, 사용자 권한 진입, 페이징 활성화는 서로 다른 상태 변화다.", y=15100)

    p = d.slide("지금 실행하는 것은 어느 컴퓨터의 코드인가?", 0, "실행 환경의 층을 구분한다 / QEMU는 게스트 커널 자체가 아니다")
    d.cards(p, [("호스트", "강사의 PC 운영체제\n터미널과 편집기\nQEMU 프로세스 실행"), ("가상 하드웨어", "QEMU TCG\nx86 CPU·메모리\n플로피·IDE·화면"), ("게스트", "Linux 0.11 커널\n루트 파일 시스템\n/bin/sh와 명령")])
    d.banner(p, "현대 호스트 위에서도 게스트가 실행하는 코드는 Linux 0.11이다.")

    p = d.slide("소스 지도: 읽는 코드와 실행하는 코드를 구분한다", 0, "build/source-changes.patch 및 build/UPSTREAM.md로 수정 이력 확인")
    d.cards(p, [("src/  원본", "boot/    부팅\ninit/      초기화\nkernel/ 태스크·진입\nmm/     메모리\nfs/        파일 시스템"), ("lab/  실행 수정본", "현대 빌드 환경 대응\nImage: 부팅 이미지\nhdc-0.11.img: 루트 디스크\n수정·재빌드 대상"), ("scripts/ · build/", "run.sh: QEMU 실행\nbuild.sh: Docker 빌드\ndebug.sh: 디버깅 준비\nbuild/: 차이와 기존 기록")])
    d.banner(p, "해설은 src/ 기준, 시연은 lab/ 기준. 차이를 숨기지 않는다.")

    p = d.slide("전체 실행 지도: 부트 섹터에서 사용자 프로그램까지", 3, "호출·제어 이전의 개략도 / 상태 변화는 뒤의 별도 그림에서 설명")
    d.flow(p, [("bootsect.s", "setup·system 적재"), ("setup.s", "하드웨어 준비\n보호 모드 진입"), ("head.s", "초기 테이블\n페이징·main 진입"), ("main.c", "커널 초기화\ninit·셸 생성")], h=3800)
    d.text(p, 1500, 10500, 30000, 3500, "이후 명령 실행은 일방향 부팅 흐름과 다르다.\n사용자 프로그램은 시스템 콜로 커널에 들어가고, 처리 후 복귀한다.", 24)
    d.banner(p, "지도 읽기 질문: 지금 누가 실행 중이며, 다음 단계의 준비 조건은 무엇인가?")

    p = d.slide("시연 1: 기초를 배웠으니 실행 결과를 본다", 3, "상세 절차: materials/01-overview/demo.md / 기존 기록과 실시간 결과를 구분")
    d.cards(p, [("호스트 터미널", "bash scripts/run.sh\n\nTCG · RAM 16 MiB\n플로피 부팅 · IDE 루트\n네트워크 없음 · snapshot"), ("게스트 셸", "echo boot-ok\nls /\n\n명령 반환과 디렉터리 확인\n관찰한 것만 성공으로 기록")])
    d.banner(p, "질문: 화면 출력, 디스크 접근, 프로세스 실행은 어디에서 준비되었을까?")

    p = d.slide("커널보다 먼저 실행되는 코드: BIOS와 부트 섹터", 3, "이 프로젝트의 legacy BIOS 부팅 기준 / UEFI와 현대 부팅 방식 전체를 설명하는 그림은 아님")
    d.flow(p, [("전원·리셋", "CPU가 정해진 위치에서\n펌웨어 실행 시작"), ("BIOS", "하드웨어 초기 준비\n부트 섹터를 RAM에 적재"), ("부트 섹터", "작은 시작 코드 실행\n나머지 커널 코드를 적재")], h=4300)
    d.text(p, 1400, 10800, 30500, 3000, "BIOS는 커널이 아니라 PC 펌웨어다.\n부트 섹터는 디스크에서 읽는 시작 영역이며, 전통적인 크기는 512바이트다.\n작은 부트 코드가 더 큰 커널 코드를 읽는 단계적 구성이 필요하다.", 22)
    d.banner(p, "QEMU는 이 부팅에 필요한 가상 PC와 펌웨어 실행 환경을 제공한다.")

    p = d.slide("부팅 세 단계는 서로 다른 일을 한다", 3, "src/boot/bootsect.s · setup.s · head.s / 오늘은 단계별 책임에 집중")
    d.cards(p, [("1  bootsect.s", "BIOS가 부트 섹터 실행\n자기 코드 이동\nsetup과 system 읽기\nsetup으로 제어 이전"), ("2  setup.s", "BIOS 정보 수집\n커널 위치 정리\nGDT·A20·PIC 준비\n보호 모드로 진입"), ("3  head.s", "32비트 코드 실행\nGDT·IDT 설정\n초기 페이지 테이블\nmain()으로 제어 이전")])

    p = d.slide("처음 보는 세 명령을 한국어로 읽어 보자", 3, "다음 장에서 원본 3줄을 확인 / 선택자 8은 GDT의 코드 항목을 가리킨다")
    d.cards(p, [("mov", "mov ax,#0x0001\n\nAX에 숫자 1 복사\n이때는 CPU 모드가\n아직 바뀐 것이 아님"), ("lmsw", "lmsw ax\n\nAX의 하위 제어 비트 사용\nPE를 1로 설정\n보호 모드 진입을 시작"), ("jmpi", "jmpi 0,8\n\n선택자 8, 오프셋 0으로\n코드 세그먼트까지 바꿔 이동\n32비트 시작 코드 실행")])
    d.banner(p, "보호 모드 자체가 항상 32비트 코드를 뜻하지는 않는다. 여기서는 32비트 항목을 사용한다.")

    p = d.slide("보호 모드 진입: 비트 설정 뒤 실행 문맥을 바꾼다", 3, "원본 코드 발췌 / lmsw의 PE 설정 + far jump를 함께 읽는다")
    d.code(p, "src/boot/setup.s", 191, 193, "PE = Protection Enable\n\n1. PE를 1로 설정\n2. 선택자 8로 far jump\n3. 32비트 head 코드로 이동\n\n아직 페이징을 켠 것은 아니다.")

    p = d.slide("페이징 활성화: 주소 변환 경로를 추가한다", 3, "src/boot/head.s:198-218 / 초기 16 MiB identity mapping 구성 후 실행")
    d.code(p, "src/boot/head.s", 213, 218, "xorl: EAX를 0으로\nmovl: 값을 복사\nCR3=0: 디렉터리 위치\norl: PG 비트를 1로\nmovl: CR0에 반영\nret: 준비한 main 주소로\n\n결과: PG 0 → 1\n보호 모드는 유지")

    p = d.slide("상태 변화도: 부팅 중 무엇이 바뀌는가?", 3, "표시 지점의 상태 / 일반 IRQ의 IF와 예외·NMI를 구분한다")
    d.flow(p, [("setup 진입", "PE=0 · PG=0\n실주소 모드"), ("head 진입", "PE=1 · PG=0\nCPL=0 · IF=0"), ("main 진입", "PE=1 · PG=1\nCPL=0 · IF=0"), ("첫 fork 직전", "PE=1 · PG=1\nCPL=3 · IF=1")], h=4000)
    d.text(p, 1400, 10800, 30500, 3200, "전환 원인: lmsw + far jump  /  CR0.PG 설정  /  sti + iret\n유지 조건: 사용자 권한으로 바뀌어도 보호 모드와 페이징은 유지된다.", 22)
    d.banner(p, "CPU 모드 ≠ 권한 수준 ≠ 페이징 상태 ≠ 인터럽트 허용 상태")

    p = d.slide("CPU 모드 전체 비교: 범위는 80386", 3, "현대 x86-64 long mode·SMM은 80386 범위 밖 / VM86은 보호 모드 내 실행 형태")
    d.cards(p, [("Real-Address", "PE=0\n초기 부팅 경로에서 사용\n실주소 방식의 실행 환경\n\n보호 모드 진입 전 단계"), ("Protected", "PE=1, VM=0\n보호·권한 검사와 테이블\n선택적으로 페이징 사용\n\nLinux 0.11 주 실행 환경"), ("Virtual-8086", "PE=1, EFLAGS.VM=1\n보호 환경에서 8086 실행\n주로 CPL 3 수준의 제약\n\n오늘의 부팅 경로는 미사용")])
    d.banner(p, "실제 경로: Real → Protected. 사용자 프로그램도 Protected에서 실행한다.")

    p = d.slide("권한 수준 전체 비교: CPL 0, 1, 2, 3", 3, "CPL은 현재 권한 수준 / 0.11의 주 경로는 ring 0과 ring 3")
    d.cards(p, [("Ring 0", "커널 코드\n높은 권한"), ("Ring 1", "중간 권한\n주 경로 미사용"), ("Ring 2", "중간 권한\n주 경로 미사용"), ("Ring 3", "사용자 코드\n제한된 권한")], h=5000)
    d.text(p, 1400, 10600, 30500, 3300, "Ring 3 → Ring 0: 시스템 콜·인터럽트·예외의 진입 경로\nRing 0 → Ring 3: 저장된 문맥으로 복귀하거나 초기 사용자 문맥을 구성", 22)
    d.banner(p, "mode 전환이라는 말만 쓰지 말고, 어떤 축이 바뀌는지 명시한다.")

    p = d.slide("독립적인 두 선택지: PG와 IF", 3, "보호 모드에서의 PG 비교 / IF는 마스크 가능한 하드웨어 인터럽트에 관한 비트")
    d.cards(p, [("페이징: CR0.PG", "0: 페이지 변환 미사용\n1: 페이지 테이블로 변환\n\n부팅 중 0 → 1\n사용자 실행 중에도 1 유지"), ("인터럽트: EFLAGS.IF", "0: 마스크 가능한 IRQ 억제\n1: 해당 IRQ 허용\n\ncli로 0, sti로 1\n예외·NMI까지 차단하지 않음")])
    d.banner(p, "네 조합의 의미는 서로 독립적이다. PG=1이 곧 IF=1을 뜻하지 않는다.")

    p = d.slide("main(): 사용자 실행을 위한 기반을 준비한다", 3, "src/init/main.c:126-136 / 호출 순서는 원본 소스에서 직접 추출")
    d.code(p, "src/init/main.c", 126, 136, "메모리 관리 준비\n예외·장치·터미널 준비\n시간과 스케줄러 준비\n버퍼와 디스크 준비\n\n준비가 끝난 뒤 sti()\n초기 단계의 IF=0과 연결한다.")

    p = d.slide("권한 변화도: 커널 초기화에서 사용자 문맥으로", 3, "src/include/asm/system.h:1-14 / move_to_user_mode()는 iret 프레임 구성")
    d.flow(p, [("초기화 코드", "Protected · PG=1\nCPL=0 · IF=0"), ("sti() 이후", "Protected · PG=1\nCPL=0 · IF=1"), ("iret 이후", "Protected · PG=1\nCPL=3 · IF=1")], h=3900)
    d.text(p, 1400, 10600, 30500, 3600, "move_to_user_mode()가 SS·ESP·EFLAGS·CS·EIP를 스택에 준비한다.\niret가 사용자 선택자와 실행 위치를 복원한다.\n같은 태스크의 권한 전환이지, fork나 새 프로그램 적재가 아니다.", 21)
    d.banner(p, "소스 파일 위치가 init/main.c여도 현재 실행 권한은 달라질 수 있다.")

    p = d.slide("프로그램·프로세스·PID: 이름이 비슷해도 다르다", 4, "0.11에서는 task라는 표현도 사용 / 프로세스 내부 구조는 5~6회차에서 확대")
    d.cards(p, [("프로그램", "디스크의 실행 파일\n예: /bin/sh\n\n같은 파일을 여러 번\n실행할 수 있다."), ("프로세스 / PID", "실행 중인 프로그램의 단위\n메모리·실행 상태를 보유\nPID: 프로세스 식별 번호\n\n부모와 자식은 별개 프로세스"), ("세 가지 연산", "fork: 자식 프로세스 생성\nexec: 프로그램 이미지 교체\nwait: 자식 종료 상태 회수\n\nCPU 모드 전환과는 다름")])
    d.banner(p, "셸도 사용자 프로그램이다. 커널 자체가 명령 문자열을 해석하는 것은 아니다.")

    p = d.slide("첫 fork(): task 0과 init의 실행 경로가 갈라진다", 4, "원본은 첫 fork 성공을 가정 / 일반 반환값은 음수·0·양수를 모두 설명")
    d.code(p, "src/init/main.c", 136, 140, "부모 반환값 > 0: 자식 PID\n→ task 0은 pause() 루프\n\n자식 반환값 = 0\n→ init() 수행\n\n실패 반환값 < 0\n→ 자식 없음, 이 코드는 복구하지 않음")

    p = d.slide("프로세스 변화도: init이 곧 셸인 것은 아니다", 4, "개략적인 분기·수명 흐름 / 자식의 실제 PID 숫자와 실행 순서는 단정하지 않는다")
    d.flow(p, [("task 0: fork()", "부모 경로 / 반환값 > 0"), ("task 0 유지", "pause() 반복 · idle 역할")], y=4600, h=2900)
    d.text(p, 1300, 7700, 30000, 700, "아래는 첫 fork의 자식 경로 (반환값 0). 부모와 별개로 계속 실행한다.", 17, TEAL)
    d.flow(p, [("PID 1 / init", "사용자 실행 관리"), ("rc 자식 생성", "init은 wait\n자식은 셸 exec"), ("대화형 셸 생성", "rc 종료 후 fork\n자식은 셸 exec")], y=8900, h=3500)
    d.text(p, 1400, 13200, 30500, 1300, "init은 살아서 wait한다. 대화형 셸 종료 → 상태 회수 → 새 셸 생성.", 21)
    d.banner(p, "구분: fork는 프로세스 생성, exec는 그 프로세스의 프로그램 이미지 교체")

    p = d.slide("터미널과 fd: 입력·출력을 작은 번호로 다룬다", 4, "fd = file descriptor / tty는 터미널 장치 / 여기서는 초기 open 성공 경로")
    d.cards(p, [("표준 입출력 번호", "fd 0: 표준 입력\nfd 1: 표준 출력\nfd 2: 표준 오류\n\n번호 자체가 장치는 아니다."), ("초기 연결 만들기", "open으로 /dev/tty0 열기\nO_RDWR: 읽기·쓰기\n\ndup(0)을 두 번 호출해\nfd 1, 2도 같은 파일에 연결"), ("접근 모드 세 가지", "O_RDONLY: 읽기 전용\nO_WRONLY: 쓰기 전용\nO_RDWR: 읽기·쓰기\n\n그 밖의 open 플래그는\n12회차에서 따로 비교")])
    d.banner(p, "입력·출력 번호가 준비되어야 셸이 키보드 입력과 화면 출력을 이용할 수 있다.")

    p = d.slide("init(): 파일과 프로세스가 만나는 지점", 4, "src/init/main.c:172-175,179-188,189-207 / fd와 wait는 뒤 회차에서 확대")
    d.code(p, "src/init/main.c", 172, 175, "setup(): 디스크·루트 준비\n\nopen(): tty를 fd 0에 연결\ndup(): fd 1, 2 구성\n\n다음 단계:\n/etc/rc용 자식 생성·대기\n대화형 셸용 자식 생성·대기")

    p = d.slide("exec 변화도: PID는 유지하고 실행 이미지를 바꾼다", 4, "src/init/main.c:194-200 / 성공은 이전 코드로 복귀하지 않으며 실패는 음수 반환")
    d.flow(p, [("셸용 자식", "init에서 fork됨\n기존 코드·주소 공간"), ("execve 호출", "실행 파일·인자·환경\n커널에서 적재 처리"), ("/bin/sh 실행", "같은 PID\n새 프로그램 이미지")], h=4200)
    d.text(p, 1400, 10900, 30500, 3000, "성공 경로: 새 사용자 프로그램 진입점에서 실행한다.\n실패 경로: execve가 반환 → 이 코드에서는 _exit()로 종료한다.", 23)
    d.banner(p, "fork와 exec를 합쳐서 하나의 함수나 하나의 상태 변화로 설명하지 않는다.")

    p = d.slide("시연 2: 화면 결과를 코드 지도에 다시 놓는다", 5, "게스트 명령 실행은 관찰 / 구체적인 시스템 콜 목록은 이 시연에서 측정하지 않음")
    d.flow(p, [("셸 입력", "echo boot-ok\nls /"), ("사용자 실행", "내장 명령 또는\n외부 프로그램"), ("커널 서비스", "요청에 따라\n파일·터미널·태스크"), ("화면 결과", "출력과 명령 반환\n다음 프롬프트")], h=3900)
    d.text(p, 1400, 10700, 30500, 3300, "모든 명령이 fork/exec를 수행한다고 가정하지 않는다.\n이 화면은 사용자 프로그램이 동작한다는 증거이지,\nCPU 제어 비트나 모든 커널 기능을 직접 검증한 결과는 아니다.", 22)

    p = d.slide("이해 확인: 관찰한 사실과 소스 추론을 구분한다", 5, "답은 강사용 notes.md 및 해당 원본 소스에서 확인")
    d.cards(p, [("기초부터 확인", "CPU는 C 소스를 직접 읽을까?\n\n주소와 그 안의 값은 같은가?\n\n두 어셈블리 문법의 차이는?"), ("흐름을 연결", "사용자 모드는 real mode인가?\n\n첫 fork 뒤 부모와 자식은?\n\nexec 뒤 PID와 프로그램은?")])
    d.banner(p, "측정하지 않은 레지스터 값은 '화면에서 확인했다'고 표현하지 않는다.")

    p = d.slide("오늘의 지도 완성: 다음에는 이 경로를 확대한다", 5, "다음 회차: x86 레지스터·스택·GDT·IDT / 현대 커널과 동일한 구현이라고 가정하지 않음")
    d.flow(p, [("BOOT", "적재·보호 모드\n페이징"), ("MAIN", "자원·장치 초기화\n사용자 권한 전환"), ("INIT", "tty·rc 준비\nfork·exec·wait"), ("SHELL", "사용자 명령\n커널 진입과 복귀")], h=4000)
    d.text(p, 1400, 10700, 30500, 3000, "기억할 세 가지\n1. 현재 실행 위치와 권한을 함께 말한다.\n2. 호출 흐름과 상태 변화를 구분한다.\n3. 원본 소스와 실행 수정본을 구분한다.", 22)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nucleus-slides-") as temp:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        process = subprocess.Popen([
            "libreoffice", "--headless", "--nologo", "--nodefault", "--norestore",
            f"-env:UserInstallation={Path(temp).as_uri()}",
            f"--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext",
        ], stdout=subprocess.DEVNULL)
        doc = None
        desktop = None
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", local)
            for _ in range(120):
                try:
                    ctx = resolver.resolve(
                        f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
                    break
                except NoConnectException:
                    if process.poll() is not None:
                        raise RuntimeError("LibreOffice exited before connection")
                    time.sleep(0.25)
            else:
                raise RuntimeError("LibreOffice connection timed out")
            desktop = ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", ctx)
            doc = desktop.loadComponentFromURL("private:factory/simpress", "_blank", 0,
                                               (prop("Hidden", True),))
            deck = Deck(doc)
            populate(deck)
            for extension, filter_name in [("pptx", "Impress MS PowerPoint 2007 XML"),
                                           ("pdf", "impress_pdf_Export")]:
                target = (args.output_dir / f"01-overview.{extension}").resolve()
                doc.storeToURL(target.as_uri(), (prop("FilterName", filter_name),
                                                prop("Overwrite", True)))
                print(f"Created {target} ({deck.pages.getCount()} slides)")
        finally:
            if doc is not None:
                doc.close(True)
            if desktop is not None:
                desktop.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
