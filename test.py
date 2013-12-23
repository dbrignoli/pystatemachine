
from state1 import *

class SimpleSM1(object):
    @staticmethod
    def state(ctx, state_id, evt):
        while True:
            ctx, state_id, evt = yield (ctx, ['-'], evt)
    @staticmethod
    def state_factory(ctx, name, evt):
        # Return the same implementaton for every state
        return SimpleSM1.state(ctx, name, evt)
    @staticmethod
    def transition(ctx, t):
        s, e = t
        tt = {
          (None, None): 's1',
          ('s1', 'n'): 's2',
          ('s2', 'n'): None,
        }
        return tt.get(t, s)

m1 = state_machine_from_class(SimpleSM1)
m2 = state_machine_from_class(SimpleSM1)
m3 = state_machine_from_class(SimpleSM1)
tt = {
    (None, None): 'm1',
    ('m1', None): 'm2',
    ('m2', None): 'm3',
    ('m3', None): None,
}
s = {
    'm1': m1,
    'm2': m2,
    'm3': m3,
}


s_f = lambda c,n,e: s[n](c,None,None)
t_f = lambda c,t: tt.get(t, t[0])
sm = state_machine(s_f, t_f)(None)
#[(val[1], val[2]) for val in iter_sm(m1(None, ('m1', None), ('m1', None)), iter([('m1','n')]*20))]
#[(val[1], val[2]) for val in iter_sm(sm, iter('n'*20))]
for val in iter_sm(sm, iter('n'*20)):
    print (val[1], val[2])
#sm.next()
#import trace
#tr = trace.Trace()
#tr.runfunc(sm.next)
