
# Copyright (c) 2013, Delio Brignoli
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Yet another `state machines with generators` module. It is intended to be a
lightweight collection of useful functions to model state machines and can be
dropped into a project's package.

I wanted something that would be easy to integrate in applications, imposing
as little as possible of the modules's conventions on client code. I also
wanted an implementation that supported nesting and sequential composition
of state machines.

Why use generators? Because they are suspend-able functions, they retain
state and deal with entry/exit to/from a state without requiring an object
oriented abstraction. An application is free to use this module's functions
within classes but it does not (and should not) have to.

The state_machine_from_class() is a convenience function for creating a state
machine from a class that encapsulates the state factory and state transition
functions.

Let's start by looking at a simple usage example:

Define a list of states and some events we want to occur in sequence. The
'test' event does not effect the state, while 'up and 'down' change the the
state to the next one up or down respectively.
>>> states = ['freezing', 'cold', 'cool', 'warm', 'hot']
>>> event_list = ['up', 'test', 'up', 'up', 'down']

A state implementation that simply prints out the last event and current
state IDs

>>> def state_ex1(ctx, state_id, evt):
...     while True:
...         ctx, vec, evt = yield (ctx, [state_id], evt)
...

Wrap callback(), state_factory() and transition() in a class to show how to
use state_machine_from_class()

>>> class StateMachineClassEx1(object):
...     @staticmethod
...     def callback(sm, val):
...         # Consume the first event and make it the current event
...         ctx, state_id, evt = val
...         if len(ctx) > 0:
...             return ctx, state_id, ctx.pop(0)
...         else:
...             raise StopIteration()
...
...     @staticmethod
...     def state_factory(ctx, name, evt):
...         # Return the same implementaton for every state
...         return state_ex1(ctx, name, evt)
...
...     @staticmethod
...     def transition(ctx, t):
...         state_id, evt = t
...         if t == (None, None):
...             # return the initial state
...             idx = states.index('cool')
...         elif evt == 'test':
...             # the 'test' event does not cause a state change
...             idx = states.index(state_id)
...         else:
...             # pick the next state form the list
...             idx = states.index(state_id)
...             if evt == 'up':
...                 idx = min(idx+1, len(states)-1)
...             else:
...                 idx = max(idx-1, 0)
...         print (state_id, evt), '->', states[idx]
...         return states[idx]
...

The event_list is passed as 'context' for the state machine
>>> sm = state_machine_from_class(StateMachineClassEx1)(event_list)
>>> end_state = run_sm(sm, StateMachineClassEx1.callback)
(None, None) -> cool
('cool', 'up') -> warm
('warm', 'test') -> warm
('warm', 'up') -> hot
('hot', 'up') -> hot
('hot', 'down') -> warm
>>> end_state
([], ['warm', 'warm'], 'down')

State and state machines are generator functions. A state is not usually
used directly but rather handled by a state machine like the one implemented
in state_machine(). A state machine is a state that handles state transitions
and dispaches execution to the currently active state. This way states can be
nested.

The skeleton_state() below shows a skeleton implementation
for a typical state. A state accepts 3 parameters: an application specific
context, an unique identifier for the state in the transition table
of the parent state machine and an event. All yield statements in a state
must yield the same 3 parameters and update the 3 parameters with the value
returned by the yield statement like this ``ctx, state_id, evt =
yield (ctx, state_id, evt)``.

>>> def skeleton_state(ctx, state_id, evt):
...     # code executed when entering the state
...     try:
...         while True:
...             # return control to the parent state machine
...             ctx, state_id, evt = yield (ctx, state_id, evt)
...
...             #
...             # code that executes every time an event is received in this state
...             #
... 
...     finally:
...         # code executed when exiting the state
...         pass

The state_machine() generator accepts an application specific context which
will be passed to each state, a state factory function called each time
an instance of a state is created (this occurs right before entering the
state) and a transition function called to retrieve the unique ID of
the next state given the current state ID and the event. The transition
function is first called with a (state_id, event) tuple of (None, None)
in order to retrieve the initial state ID. When the transition function
returns None the state machine has reached its final state and stops.

run_sm() is used to run a state machine to completion. The optional callback
function parameter is invoked for each event and the optional val parameter
is useful for resuming execution of a state machine. The callback function
must return a tuple containing the context, state ID and event parameters,
the values returned can be different from the values it was passed.
The callback function can raise StopIteration() to indicate that the run_sm()
should exit. run_sm() returns the last valid context, state ID and event
tuple.

state_machine_from_class() returns a state machine instance initialised using
the `state_factory` and `transition` methods of the class.

============================================================================


>>> class SimpleSM1(object):
...     @staticmethod
...     def state(ctx, state_id, evt):
...         while True:
...             ctx, state_id, evt = yield (ctx, ['-'], evt)
...     @staticmethod
...     def state_factory(ctx, name, evt):
...         # Return the same implementaton for every state
...         return SimpleSM1.state(ctx, name, evt)
...     @staticmethod
...     def transition(ctx, t):
...         s, e = t
...         tt = {
...           (None, None): 's1',
...           ('s1', 'n'): 's2',
...           ('s2', 'n'): None,
...         }
...         return tt.get(t, s)
... 
>>> m1 = state_machine_from_class(SimpleSM1)
>>> m2 = state_machine_from_class(SimpleSM1)
>>> m3 = state_machine_from_class(SimpleSM1)
>>> tt = {
...     (None, None): 'm1',
...     ('m1', None): 'm2',
...     ('m2', None): 'm3',
...     ('m3', None): None,
... }
>>> s = {
...     'm1': m1,
...     'm2': m2,
...     'm3': m3,
... }
>>> s_f = lambda c,n,e: s[n](c,None,None)
>>> t_f = lambda c,t: tt.get(t, t[0])
>>> sm = state_machine(s_f, t_f)(None)
>>> for val in iter_sm(sm, iter('n'*20)):
...     print (val[1], val[2])
...
(['-', 's1', 'm1'], None)
(['-', 's2', 'm1'], 'n')
(['-', 's1', 'm2'], None)
(['-', 's2', 'm2'], 'n')
(['-', 's1', 'm3'], None)
(['-', 's2', 'm3'], 'n')


>>> tt = {
...     (None, None): 'closed',
...     ('closed', 'open'): 'opened',
...     ('opened', 'close'): 'closed',
...     ('closed', 'lock'): 'locked',
...     ('locked', 'unlock'): 'closed',
... }
>>> s_f = lambda c,n,e: state_ex1(c, n, e)
>>> t_f = lambda c,t: tt.get(t, t[0])
>>> def print_transitions(iter):
...     old_s = None
...     while True:
...         c, s, e = iter.next()
...         print (old_s, e), '->', s[-1]
...         old_s = s[-1]
...         yield (c, s, e)
...
>>> e = ['lock', 'open', 'unlock', 'open', 'close']
>>> sm = state_machine(s_f, t_f)(None)
>>> l = [val for val in print_transitions(iter_sm(sm, iter(e)))]
(None, None) -> closed
('closed', 'lock') -> locked
('locked', 'open') -> locked
('locked', 'unlock') -> closed
('closed', 'open') -> opened
('opened', 'close') -> closed

# Using run_sm()

>>> def cb(sm, val):
...     ctx, state_id, evt = val
...     print (ctx['last_state'], evt), '->', state_id[-1]
...     ctx['last_state'] = state_id[-1]
...     return ctx, state_id, ctx['evt_src'].next()
...
>>> ctx = dict([('evt_src', iter(e)), ('last_state', None)])
>>> sm = state_machine(s_f, t_f)(ctx)
>>> val = run_sm(sm, cb)
(None, None) -> closed
('closed', 'lock') -> locked
('locked', 'open') -> locked
('locked', 'unlock') -> closed
('closed', 'open') -> opened
('opened', 'close') -> closed

"""


import unittest
import doctest


def state_machine(state_factory, transition_func):
    def sm(ctx, state_id=None, evt=None):
        state = None
        #print ctx, (state_id, evt)
        try:
            while True:
                next_state_id = transition_func(ctx, (state_id, evt))
                #print ctx, (state_id, evt), next_state_id
                if next_state_id is None:
                    break
                try:
                    if (next_state_id != state_id):
                        if state is not None:
                            state.close()
                        state_id = next_state_id
                        state = state_factory(ctx, state_id, evt)
                        ctx, state_id_vec, evt = state.next()
                    else:
                        ctx, state_id_vec, evt = state.send((ctx, state_id, evt))
                except StopIteration:
                    evt = None
                    continue
                ctx, state_id_vec, evt = yield (ctx, state_id_vec + [state_id], evt)
                if state_id is None:
                    break
        finally:
            if state is not None:
                state.close()
    return sm


def state_machine_from_class(cls):
    return state_machine(cls.state_factory, cls.transition)


def run_sm(sm, callback=None, val=None):
    try:
        while True:
            val = sm.send(val)
            if callback:
                val = callback(sm, val)
    except StopIteration:
        pass
    return val


def iter_sm(sm, evt_iter = None, callback = None):
    val = None
    while True:
        val = sm.send(val)
        if callback:
            val = callback(sm, val)
        pval = yield val
        if pval is not None:
            val = pval
        elif evt_iter is not None:
            val = (val[0], val[1], evt_iter.next())


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite())
    return tests

if __name__ == "__main__":
    unittest.main()
