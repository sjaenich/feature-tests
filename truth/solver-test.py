from z3.z3 import Solver
from z3.z3 import StringVal
from z3.z3 import String
from z3.z3 import *
solver = Solver()

s = String("s")
InBinary = Function('InBinary', StringSort(), IntSort(), BoolSort())
solver.add(InBinary(StringVal("<!DOCTYPE root [<!ELEMENT root EMPTY>]><root xmlns:h=http://example.com/ h:foo=bar/>"), IntVal(1)) == And(True))
if solver.check() == sat:
    print("SAT")
else:
    print("UNSAT")