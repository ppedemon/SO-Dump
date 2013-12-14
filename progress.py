
import sys
import termios
import time

from fcntl import ioctl
from struct import unpack

class Progress():
  def __init__(self,total):
    self.total = total
    self.cols = unpack('hh', 
      ioctl(sys.stdout, termios.TIOCGWINSZ, '1234'))[1]
  
  def _bold(self,msg):
    return u'\033[1m%s\033[0m' % msg

  def progress(self,prog):
    prefix = '%.1f%%' % (float(prog)/self.total*100)
    begin = ' ['
    end = ']'
    size = self.cols - len(prefix + begin + end)
    covered = int(float(prog)/self.total*size)
    rest = size - covered
    bar = '='*covered + ' '*rest
    msg = self._bold(prefix) + begin + bar + end + '\r'
    sys.stdout.write(msg)
    sys.stdout.flush()

