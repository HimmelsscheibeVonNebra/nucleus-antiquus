# 빌드용 소스 출처

- 저장소: https://github.com/yuan-xy/Linux-0.11
- 고정 커밋: `c2e45a7f55ba61029be3b74cd7e72f23bbd068d6`
- 루트 디스크: 위 저장소의 `hdc-0.11.img`
- 디스크 SHA-256: `0f57a2ebca218ed52844d4769f35fce32d9fce850d9cc0509c6c3c6e4a07c7f4`
- `src/`는 Kernel.org 원본이며 `lab/`은 현대 빌드 도구용 수정본이다. 두 소스는 동일하지 않다.
- 로컬 컴파일 옵션은 `scripts/build.sh`에 기록한다.

## 원본과 비교

`source-changes.patch`에 원본 파일 기준 차이를 기록했다. 빌드용 저장소에 추가된 파일과 디스크 이미지는 이 패치에 포함하지 않는다.

- 수정: `Makefile`
- 수정: `boot/bootsect.s`
- 수정: `boot/head.s`
- 수정: `boot/setup.s`
- 수정: `fs/Makefile`
- 수정: `fs/bitmap.c`
- 수정: `fs/buffer.c`
- 수정: `fs/char_dev.c`
- 수정: `fs/exec.c`
- 수정: `fs/fcntl.c`
- 수정: `fs/file_dev.c`
- 수정: `fs/inode.c`
- 수정: `fs/ioctl.c`
- 수정: `fs/namei.c`
- 수정: `fs/open.c`
- 수정: `fs/super.c`
- 수정: `fs/truncate.c`
- 수정: `include/asm/memory.h`
- 수정: `include/asm/segment.h`
- 수정: `include/asm/system.h`
- 수정: `include/linux/config.h`
- 수정: `include/linux/kernel.h`
- 수정: `include/linux/sched.h`
- 수정: `include/linux/sys.h`
- 수정: `include/string.h`
- 수정: `include/unistd.h`
- 수정: `init/main.c`
- 수정: `kernel/Makefile`
- 수정: `kernel/asm.s`
- 수정: `kernel/blk_drv/Makefile`
- 수정: `kernel/blk_drv/blk.h`
- 수정: `kernel/blk_drv/floppy.c`
- 수정: `kernel/blk_drv/hd.c`
- 수정: `kernel/blk_drv/ll_rw_blk.c`
- 수정: `kernel/chr_drv/Makefile`
- 수정: `kernel/chr_drv/console.c`
- 수정: `kernel/chr_drv/keyboard.S`
- 수정: `kernel/chr_drv/rs_io.s`
- 수정: `kernel/chr_drv/tty_io.c`
- 수정: `kernel/exit.c`
- 수정: `kernel/fork.c`
- 수정: `kernel/math/Makefile`
- 수정: `kernel/mktime.c`
- 수정: `kernel/panic.c`
- 수정: `kernel/printk.c`
- 수정: `kernel/signal.c`
- 수정: `kernel/system_call.s`
- 수정: `kernel/traps.c`
- 수정: `kernel/vsprintf.c`
- 수정: `lib/Makefile`
- 수정: `lib/_exit.c`
- 수정: `lib/malloc.c`
- 수정: `lib/string.c`
- 수정: `mm/Makefile`
- 수정: `mm/memory.c`
- 수정: `mm/page.s`
- 삭제/대체: `tools/build.c`
