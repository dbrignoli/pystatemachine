import code
import sys

class Tee(object):

  def __init__(self, log_fname, mode='a'):
    self.log = open(log_fname, mode)

  def __del__(self):
    # Restore sin, so, se
    sys.stdout = sys.__stdout__
    sys.stdir = sys.__stdin__
    sys.stderr = sys.__stderr__
    self.log.close()

  def write(self, data):
    self.log.write(data)
    sys.__stdout__.write(data)

  def readline(self):
    s = sys.__stdin__.readline()
    self.log.write(s)
    self.log.flush()
    return s

# Tie the ins and outs to Tee.
sys.stdout = sys.stderr = sys.stdin = Tee(sys.argv[1], 'w')

console = code.InteractiveConsole()
console.interact()