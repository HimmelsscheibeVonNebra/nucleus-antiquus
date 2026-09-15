# 운영체제별 Linux 0.11 빌드와 QEMU 실행

이 문서는 이 프로젝트를 **Windows / Ubuntu Linux / 하모니카 Linux(HamoniKR) / macOS**에서 실행하는 방법을 설명한다. 호스트 운영체제 위에서 QEMU로 Linux 0.11을 부팅하며, 소스를 다시 빌드할 때는 Docker의 `linux/amd64` 환경을 사용한다.

**이미 `lab/Image`와 `lab/hdc-0.11.img`가 있다면 QEMU만 설치하면 된다. Docker는 재빌드할 때 필요하다.**

## 1. 환경과 검증 범위

| 호스트 환경 | 명령을 입력할 곳 | 실행 도구 | 재빌드 도구 | 검증 상태 |
|---|---|---|---|---|
| Windows 11 x86-64 | WSL2 Ubuntu 터미널 | WSL의 QEMU + WSLg 창 | Windows Docker Desktop의 WSL 연동 | 절차 작성, 실기 미검증 |
| Ubuntu Desktop x86-64 | Ubuntu 터미널 | 배포판 QEMU | Docker Engine | 절차 작성, 실기 미검증 |
| 하모니카 Linux x86-64 | 하모니카 터미널 | 배포판 QEMU | Docker Engine | 절차 작성, 실기 미검증 |
| macOS Apple Silicon | 터미널 | Homebrew QEMU | Docker Desktop | 기존 부팅·빌드 확인 기록 있음 |
| macOS Intel | 터미널 | Homebrew QEMU | Docker Desktop | 절차 작성, 실기 미검증 |

Ubuntu 설치 명령은 24.04 LTS를 기준으로 정리했다. 하모니카는 Ubuntu 기반 배포판의 APT 패키지를 사용하는 절차이며, 버전별 패키지 제공 여부를 확인한다. Windows ARM과 ARM Linux의 빌드 환경은 이 안내의 확인 범위 밖이다.

기존 macOS 검증 환경은 Apple Silicon arm64, Homebrew QEMU 11.1.1, Docker Desktop, Debian bookworm amd64/GCC 12다. 셸 진입 및 `ls /`, `echo boot-ok` 실행 기록은 [부팅 화면](build/boot.png)과 [빌드 로그](build/build.log)에 있다. 모든 커널 기능이나 GDB 중단점 연결을 검증한 것은 아니다.

## 2. 공통 준비

배포받은 **프로젝트 폴더 전체**를 작업할 컴퓨터에 복사하거나 압축 해제한다. 아래 파일이 필요하다.

```text
nucleus-antiquus/
├── Dockerfile
├── scripts/build.sh
├── scripts/run.sh
├── scripts/debug.sh
├── src/                 # 읽기 기준인 원본 소스
└── lab/
    ├── Image            # 부팅 이미지: 없으면 빌드 필요
    ├── hdc-0.11.img      # 루트 디스크: 빌드로 생성되지 않음
    └── ...              # 재빌드용 소스 전체
```

이후 Bash 명령은 프로젝트 최상위 폴더에서 실행한다. 아래 경로는 예시이므로 실제 압축을 푼 위치로 바꾼다.

```bash
cd ~/lectures/nucleus-antiquus
ls scripts/run.sh lab/hdc-0.11.img
```

문서에서는 실행 권한이 보존되지 않은 압축 파일도 사용할 수 있도록 `bash scripts/run.sh` 형식을 사용한다. 원래의 `./scripts/run.sh` 형식 및 디버깅 스크립트를 사용하려면 다음을 한 번 실행한다.

```bash
chmod +x scripts/build.sh scripts/run.sh scripts/debug.sh
```

## 3. Windows

### 3.1 WSL2 Ubuntu 준비

Windows 11 x86-64를 기준으로 한다. 관리자 권한 **PowerShell**에서 실행한다.

```powershell
wsl --install -d Ubuntu-24.04
```

설치 안내에 따라 재부팅하고 Ubuntu를 열어 Linux 사용자 이름과 암호를 만든다. 이미 WSL이 있다면 PowerShell에서 확인한다.

```powershell
wsl --update
wsl -l -v
```

사용할 Ubuntu의 `VERSION`이 `2`여야 한다. `1`이면 목록에 표시된 정확한 배포판 이름으로 변환한다. 예를 들어 다음과 같다.

```powershell
wsl --set-version Ubuntu-24.04 2
```

QEMU 창은 WSLg를 통해 표시된다. Microsoft의 GUI 지원 조건은 Windows 10 빌드 19044 이상 또는 Windows 11과 WSL2다. Windows 10에서 재빌드까지 하려면 별도로 현재 Docker Desktop의 Windows 지원 조건도 확인한다. [WSL GUI 공식 안내](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps), [Docker Desktop Windows 설치](https://docs.docker.com/desktop/setup/install/windows-install/).

### 3.2 프로젝트 복사 및 QEMU 설치

이제부터는 **WSL Ubuntu 터미널**에서 실행한다. 프로젝트가 Windows의 다운로드 폴더에 있다면 다음과 같이 WSL 홈으로 복사할 수 있다. `WINDOWS_USER`는 실제 Windows 사용자 폴더 이름으로 바꾼다.

```bash
mkdir -p ~/lectures
cp -r /mnt/c/Users/WINDOWS_USER/Downloads/nucleus-antiquus ~/lectures/
cd ~/lectures/nucleus-antiquus
sudo apt update
sudo apt install -y qemu-system-x86 qemu-system-gui
bash scripts/run.sh
```

셸 스크립트를 PowerShell에서 직접 실행하지 않는다. 수정과 빌드도 복사한 WSL 쪽 프로젝트에서 진행한다.

### 3.3 재빌드가 필요할 때

1. [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/)를 설치하고 실행한다.
2. Settings → General에서 **Use WSL 2 based engine**을 사용한다. 환경에 따라 이미 활성화되어 항목이 표시되지 않을 수 있다.
3. Settings → Resources → WSL Integration에서 사용할 Ubuntu 배포판을 활성화하고 적용한다.
4. WSL Ubuntu 터미널에서 아래 명령을 실행한다.

```bash
docker version
bash scripts/build.sh
bash scripts/run.sh
```

`docker version`에 Client와 Server가 모두 표시되어야 한다. 이 구성에서는 WSL Ubuntu에 `docker.io`를 추가 설치하지 않는다. [Docker의 WSL 연동 문서](https://docs.docker.com/desktop/features/wsl/).

## 4. Ubuntu Linux

### 4.1 QEMU 설치 및 실행

Ubuntu **데스크톱 세션의 터미널**에서 실행한다.

```bash
sudo apt update
sudo apt install -y qemu-system-x86 qemu-system-gui
cd ~/lectures/nucleus-antiquus
bash scripts/run.sh
```

`qemu-system-x86`는 x86 시스템 에뮬레이터, `qemu-system-gui`는 창 표시용 모듈을 제공한다. [QEMU 설치 안내](https://www.qemu.org/download/), [Ubuntu GUI 패키지](https://packages.ubuntu.com/noble/qemu-system-gui).

### 4.2 재빌드가 필요할 때

Docker가 아직 없는 PC에서는 Ubuntu 배포판의 `docker.io` 패키지를 사용하는 다음 절차로 준비할 수 있다. Docker 공식 저장소의 `docker-ce`나 Docker Desktop을 이미 사용 중이면 기존 설치를 유지하고 이 설치 단계는 건너뛴다. 두 패키지 계열을 섞지 않는다. [Ubuntu docker.io 패키지](https://packages.ubuntu.com/noble/docker.io), [Docker 공식 설치 및 충돌 패키지 안내](https://docs.docker.com/engine/install/ubuntu/).

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo docker version
cd ~/lectures/nucleus-antiquus
sudo bash scripts/build.sh
bash scripts/run.sh
```

위 명령은 Docker 접근에 `sudo`를 사용하는 방식이다. 이미 일반 사용자로 Docker를 사용할 수 있다면 `bash scripts/build.sh`로 실행한다. QEMU 실행에는 `sudo`를 붙이지 않는다.

컨테이너 빌드 후 `lab/`의 생성 파일이 root 소유라서 편집 또는 삭제가 막히면 프로젝트 최상위에서 소유권을 되돌린다.

```bash
sudo chown -R "$(id -u):$(id -g)" lab
```

## 5. 하모니카 Linux

### 5.1 버전 확인 및 QEMU 실행

하모니카 데스크톱의 터미널에서 배포판 정보와 CPU를 확인한다.

```bash
cat /etc/os-release
uname -m
```

이 절차는 `x86_64` PC를 대상으로 한다. 하모니카 버전에 관한 설명은 [공식 사용자 문서](https://docs.hamonikr.org/hamonikr-8.0)에서 확인할 수 있다.

```bash
sudo apt update
apt-cache policy qemu-system-x86 qemu-system-gui docker.io
```

필요한 패키지의 `Candidate`가 `(none)`이 아닌지 확인한 후 설치한다.

```bash
sudo apt install -y qemu-system-x86 qemu-system-gui
cd ~/lectures/nucleus-antiquus
bash scripts/run.sh
```

### 5.2 재빌드가 필요할 때

Docker가 설치되지 않은 환경에서 배포판 저장소의 패키지를 설치한다.

```bash
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo docker version
cd ~/lectures/nucleus-antiquus
sudo bash scripts/build.sh
bash scripts/run.sh
```

이미 Docker를 사용 중이면 설치를 생략하고 기존 Docker 환경으로 빌드한다. 생성 파일의 권한 문제는 Ubuntu 절의 `chown` 명령으로 처리한다.

패키지 후보가 없으면 사용 중인 하모니카 버전의 소프트웨어 소스 설정을 먼저 확인한다. Docker는 Ubuntu 파생 배포판을 공식 지원 대상으로 보장하지 않으므로, Docker 공식 저장소를 별도로 추가할 경우 하모니카 코드명을 Ubuntu 코드명으로 그대로 사용해서는 안 된다. 이 안내는 하모니카에서 Docker Desktop 대신 배포판의 Docker Engine 패키지를 이용한다. [Docker 지원 배포판 안내](https://docs.docker.com/engine/install/ubuntu/).

## 6. macOS

### 6.1 QEMU 설치 및 실행

[Homebrew](https://brew.sh/)가 없으면 공식 사이트의 설치 안내에 따라 설치하고, 설치 마지막에 표시되는 PATH 설정을 적용한다. macOS 터미널에서 실행한다.

```bash
brew install qemu
qemu-system-i386 --version
cd ~/lectures/nucleus-antiquus
bash scripts/run.sh
```

Homebrew 설치 명령은 [QEMU 공식 다운로드 문서](https://www.qemu.org/download/)에서도 안내한다. Intel과 Apple Silicon 모두 스크립트의 TCG로 x86 CPU를 에뮬레이션한다.

### 6.2 재빌드가 필요할 때

[Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)에서 CPU에 맞는 Apple Silicon 또는 Intel 설치 파일을 선택한다. 설치 후 Docker 앱을 실행하고 엔진이 준비될 때까지 기다린다.

```bash
docker version
cd ~/lectures/nucleus-antiquus
bash scripts/build.sh
bash scripts/run.sh
```

스크립트와 Dockerfile이 `linux/amd64`를 지정하므로 Apple Silicon에서도 x86 Linux 빌드 환경을 사용한다. 호스트의 Apple Clang이나 ARM Linux 컴파일러로 대체하지 않는다.

## 7. 부팅 확인과 종료 — 모든 OS 공통

QEMU 창을 클릭하고 입력 소스를 영문으로 바꾼다. 부팅 후 게스트 셸에서 실행한다.

```sh
pwd
ls /
echo boot-ok
```

`boot-ok`가 보이면 기본 부팅 및 입력 확인이 끝난 것이다. 이 루트 디스크에는 `uname`이 없으므로 부팅 확인용으로 사용하지 않는다. 호스트 터미널과 QEMU 안의 Linux 0.11 셸은 서로 다른 환경이다.

종료할 때는 QEMU 창을 닫거나 macOS의 QEMU → Quit 메뉴를 사용한다. 포인터가 잡혀 있으면 QEMU 창에 표시된 입력 해제 단축키를 사용한다. 새 실습을 시작하기 전에 이전 QEMU 인스턴스를 종료한다.

현재 `scripts/run.sh`의 주요 설정은 다음과 같다.

| 설정 | 의미 |
|---|---|
| `-accel tcg` | 소프트웨어로 x86 CPU 에뮬레이션 |
| `-m 16M` | 게스트 메모리 16 MiB |
| `-boot a`와 `lab/Image` | 플로피 이미지에서 부팅 |
| `lab/hdc-0.11.img` | IDE 루트 디스크 연결 |
| `-nic none` | 게스트 네트워크 장치 없음 |
| `-snapshot` | 게스트의 디스크 변경은 QEMU 종료 시 사라짐 |

게스트 안에 만든 파일도 종료하면 사라진다. 호스트의 `lab/` 소스 수정은 그대로 남는다.

## 8. 소스 수정과 재빌드

- `src/`: Kernel.org Linux 0.11 원본, 소스 분석 기준.
- `lab/`: 현대 도구로 빌드할 수 있도록 수정된 별도 upstream 소스.
- `lab/Image`: 빌드 결과인 부팅 이미지.
- `lab/tools/system`: 디버깅 심볼이 포함된 ELF 파일.
- `lab/hdc-0.11.img`: upstream이 제공한 루트 디스크. `build.sh`가 생성하지 않는다.

**`src/`를 수정해도 실행 이미지에는 반영되지 않는다.** 실행 실험은 `lab/`을 수정한 뒤 재빌드한다. 출처와 고정 커밋은 [UPSTREAM.md](build/UPSTREAM.md), 원본과의 차이는 [소스 변경 패치](build/source-changes.patch)를 참고한다. 부팅 화면의 `IceCityOS`는 빌드용 upstream이 넣은 문자열이다.

```bash
bash scripts/build.sh
bash scripts/run.sh
```

Ubuntu·하모니카에서 앞서 `sudo` 방식으로 Docker를 사용했다면 빌드 명령에도 `sudo`를 붙인다. 첫 빌드는 네트워크로 Debian 이미지와 패키지를 내려받고, 이후에는 Docker 캐시를 이용한다.

컴파일 옵션이나 헤더를 변경했는데 수정이 반영되지 않으면 기존 결과물을 정리하고 빌드한다. 아래 정리 명령은 `linux-011-builder` 이미지가 한 번 생성된 뒤 사용할 수 있다.

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD/lab:/work" -w /work linux-011-builder make clean
bash scripts/build.sh
```

Docker에 관리자 권한이 필요한 Linux 환경에서는 위 두 명령에 각각 `sudo`를 붙인다. 기록된 빌드에는 오래된 inline 선언 등의 경고가 포함된다. 성공 여부는 명령의 종료 상태와 새 이미지의 부팅으로 판단한다.

## 9. 선택 사항: GDB 연결

이 절차는 연결 방법 안내이며 실제 중단점 적중은 아직 검증하지 않았다. WSL Ubuntu·Ubuntu·하모니카에서는 QEMU가 실행되는 동일한 환경에 GDB를 설치한다.

```bash
sudo apt install -y gdb
chmod +x scripts/run.sh
bash scripts/debug.sh
```

QEMU는 CPU를 실행하기 전에 멈추고 `127.0.0.1:1234`에서 접속을 기다린다. 화면이 멈춰 있는 것은 정상이다. 같은 환경의 다른 터미널에서 프로젝트 폴더로 이동한 후 실행한다.

```bash
gdb lab/tools/system
```

GDB 프롬프트에서 입력한다.

```gdb
target remote 127.0.0.1:1234
hbreak main
continue
```

부팅 중 코드가 메모리에 적재되므로 최초 `main` 진입에는 하드웨어 중단점을 사용한다. 소스는 실행 이미지와 일치하는 `lab/`을 기준으로 읽는다. 소스 경로가 `/work`로 표시되어 찾지 못하면 GDB에서 실제 호스트 경로로 연결한다.

```gdb
set substitute-path /work /home/YOUR_USER/lectures/nucleus-antiquus/lab
```

`YOUR_USER`와 경로는 실제 위치로 바꾼다. macOS에서는 x86 타깃을 지원하는 GDB를 별도로 준비해야 하며 이 문서에 설치 검증 절차는 포함하지 않는다. Docker 안의 GDB는 컨테이너의 loopback이 호스트와 다르므로 위 주소로 바로 연결할 수 없다. [QEMU GDB 공식 문서](https://www.qemu.org/docs/master/system/gdb.html).

## 10. 자주 발생하는 문제

| 증상 | 확인 및 해결 |
|---|---|
| `qemu-system-i386: command not found` | 해당 OS의 QEMU 설치 단계를 실행하고 새 터미널에서 `qemu-system-i386 --version` 확인 |
| `먼저 ./scripts/build.sh를 실행하세요.` | `lab/Image`가 없다. Docker 준비 후 `bash scripts/build.sh` 실행 |
| `lab/hdc-0.11.img`를 열 수 없음 | 프로젝트에 포함된 루트 디스크를 복원. 커널 재빌드만으로 생성되지 않음 |
| `Permission denied`로 스크립트 실행 실패 | `bash scripts/run.sh` 사용 또는 `chmod +x scripts/*.sh` 실행 |
| `bash\r` 또는 `$'\r'` 관련 오류 | 편집기에서 셸 스크립트의 줄바꿈을 CRLF에서 LF로 변환해 저장 |
| Docker 데몬 연결 실패 | Windows/macOS는 Docker Desktop 실행과 `docker version`의 Server 확인. Linux는 `sudo systemctl start docker` 실행 |
| Docker 소켓 접근 거부 | Linux는 문서의 `sudo bash scripts/build.sh` 사용. WSL Docker Desktop은 WSL Integration 확인 |
| WSL에서 `docker` 명령이 없음 | Windows Docker Desktop의 해당 Ubuntu WSL Integration을 켜고 터미널 다시 열기 |
| `gtk initialization failed` 또는 창이 안 뜸 | Linux 데스크톱 세션인지, `qemu-system-gui` 설치 여부 확인. WSL은 `wsl --update`와 WSL2 여부 확인 |
| SSH/화면 없는 서버에서 창이 안 뜸 | 이 안내는 GUI 세션 기준. `-nographic`만으로 Linux 0.11의 VGA 콘솔이 시리얼 콘솔로 바뀌지는 않음 |
| `exec format error`로 Docker 빌드 실패 | `linux/amd64` 컨테이너 실행 지원 확인. Apple Silicon은 Docker Desktop 엔진 상태 확인 |
| 수정한 소스가 반영되지 않음 | `src/`가 아닌 `lab/`을 수정했는지 확인하고 필요하면 `make clean` 후 재빌드 |
| 디버깅 실행 후 화면이 멈춤 | `-S`의 정상 동작. GDB 연결 후 `continue`, 일반 부팅은 `run.sh` 사용 |
| `Address already in use`로 디버깅 실패 | 기존 디버깅 QEMU가 1234 포트를 사용 중인지 확인하고 종료 |

설치 안내의 공식 문서 확인일: 2026-09-13. OS별 실기 검증 상태는 문서 첫 표를 기준으로 한다.
