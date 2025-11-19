# tpkg/logger.py

# Simple color logger with depth-based colors

RESET = "\033[0m"
WHITE = "\033[97m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"

def log(msg, depth=0):
    """
    Print colored log message based on recursion depth.
    Depth controls color:
      0 = white  | main nouns
      1 = cyan   | child nouns
      2 = yellow | grandchildren
      3+ = red   | deep recursion
    """

    if depth == 0:
        color = WHITE
    elif depth == 1:
        color = CYAN
    elif depth == 2:
        color = YELLOW
    else:
        color = RED

    print(color + msg + RESET)
