import sys, termios,os,select
import logging,inspect
def getch(timeout=20):
    fd = sys.stdin.fileno()
    orig = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    # new[3] = new[3] & ~termios.ICANON
    new[3] = new[3] & ~termios.ICANON & ~termios.ECHO  # Turn off ECHO flag(回显)
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0

    try:
        termios.tcsetattr(fd, termios.TCSAFLUSH, new)
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            return sys.stdin.read(1)
        else:
            # print(f"Timeout {timeout}s")
            return None
    except Exception as e:
        return None
    except KeyboardInterrupt as e:
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, orig)

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def is_debug(mode=None):
    debug = os.getenv("DEBUG", False)
    if mode is None:
        return debug
    return debug and str(mode) == debug

def debug_print(*args, mode=None):
    if is_debug(mode):
      callerframerecord = inspect.stack()[1]    # 1 caller, 0 self
      frame = callerframerecord[0]
      info = inspect.getframeinfo(frame)
      color_red = f"\033[91m"
      color_end = f"\033[0m"
      print(f'{color_red}{info.filename}:{info.lineno}:{info.function}{color_end}', args)

if is_debug():
    formatmsg='%(asctime)s:%(levelname)s:%(pathname)s:%(lineno)s:%(message)s'
    logging.basicConfig(format=formatmsg, level=logging.DEBUG)