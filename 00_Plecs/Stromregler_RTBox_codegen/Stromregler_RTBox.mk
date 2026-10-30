CROSS            ?= "C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/bin/win/arm-none-eabi/bin/arm-none-eabi-"
CFLAGS           := -Wall -O2 -c -g -fmessage-length=0 -DEXTERNAL_MODE=1 \
   -DPLX_RTBOX \
   -fgcse-after-reload \
   -finline-functions \
   -fipa-cp-clone \
   -floop-interchange \
   -floop-unroll-and-jam \
   -fpeel-loops \
   -fpredictive-commoning \
   -fsplit-paths \
   -ftree-loop-distribute-patterns \
   -ftree-loop-distribution \
   -ftree-loop-vectorize \
   -ftree-partial-pre \
   -ftree-slp-vectorize \
   -funswitch-loops \
   -fvect-cost-model \
   -fno-fast-math \
   -fno-common \
   -mtune=cortex-a9 -mcpu=cortex-a9 \
   -Wno-unused-variable \
   -funsafe-math-optimizations -fopt-info-vec --param max-completely-peeled-insns=1000 --param max-completely-peel-times=100
CC               = $(CROSS)gcc
LD               = $(CROSS)ld
STRIP            = $(CROSS)strip
INCLUDE          := -I"C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/include/rtbox"
LIBS             := "C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/bin/win/arm-none-eabi/bin/../lib/gcc/arm-none-eabi/8.3.0/crti.o" \
                    -L"C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/lib/rtbox" -L"C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/lib/rtbox/OpenAmp" \
                    -L"C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/bin/win/arm-none-eabi/bin/../arm-none-eabi/lib" \
                    -L"C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/bin/win/arm-none-eabi/bin/../lib/gcc/arm-none-eabi/8.3.0" \
                    -L"C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/lib/rtbox/Xilinx" -lplexim_hil -lopen_amp -lbaremetal_remote\
                    -lm --start-group -lxil -lc -lgcc --end-group \
                    "C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/bin/win/arm-none-eabi/bin/../lib/gcc/arm-none-eabi/8.3.0/crtn.o"
LFLAGS           := -T "C:/Users/hanne/OneDrive - ZHAW/Dokumente/Plexim/PLECS 5.0 (64 bit)/coderTargets/PLECS_RT_Box/build/rtbox.ld"

undefine GCC_EXEC_PREFIX

ifeq ($(OS),Windows_NT)
 SHELL            := cmd.exe
 RM               := DEL /F
else
 RM               := rm -f
endif

APP = Stromregler_RTBox_linked.elf
BIN = Stromregler_RTBox.elf

HEADERS += Stromregler_RTBox.h
C_SRCFILES += Stromregler_RTBox_main.c Stromregler_RTBox.c

OBJFILES := $(patsubst %.c, %.o, $(C_SRCFILES))
DEPFILES := $(patsubst %.c, %.d, $(C_SRCFILES))

all: $(BIN)

$(APP): $(OBJFILES)
	@echo Linking $@
	$(LD) -o $@ $(LFLAGS) $(OBJFILES) $(LIBS)
    
$(BIN): $(APP)
	@$(STRIP) -o $@ $<

%.o:%.c $(HEADERS)
	@echo Compiling $(<:.c=.o)
	@$(CC) $(CFLAGS) $(ARCH_CFLAGS) $(INCLUDE) -c $< -o $@

clean:
	-$(RM) $(LIB) $(OBJFILES)

FORCE:

PHONY: all clean
