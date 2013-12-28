#!/usr/bin/env python

"""A state machine module based on generator functions

.. codeauthor:: Delio Brignoli <brignoli.delio@gmail.com>


Introduction
============

Yet another `state machines with generators` module. It is intended to be a
lightweight collection of useful functions to model state machines and can be
dropped into your project's package.

I wanted something that would be easy to integrate in applications, imposing
as little as possible of the modules's conventions on client code. I also
wanted an implementation that supported nesting and sequential composition
of state machines.

Why use generators? Because they are suspend-able functions, they retain
state and deal with entry/exit to/from a state without requiring an object
oriented abstraction. An application is free to use this module's functions
within classes but it does not (and should not) have to.

The state_machine_from_class() function can be used to create
a state machine instance form a class encapsulating the state factory and
state transition functions.


Tutorial
========

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
...             # code that executes every time an event is received
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

# Hierarchical state machine example: pocket calculator

>>> import operator
>>> import sys
>>> def display(str_or_int):
...     sys.stdout.write(' ' + str(str_or_int))
...
>>> class PocketCalcInnerSM(object):
...
...     tt = {
...         ('on', None): 'op_nd1',
...         ('op_nd1', '/*+-'): 'op_tor',
...         ('op_tor', '0123456789.'): 'op_nd2',
...         ('op_nd2', '/*+-'): 'op_tor',
...         ('op_nd2', '='): 'result',
...         ('result', '/*+-'): 'op_tor',
...         ('result', '0123456789.'): 'op_nd1',
...     }
...
...     @classmethod
...     def transition(cls, c, t):
...         s_id = cls.tt.get(t, None)
...         if s_id is None:
...             for k,v in cls.tt.items():
...                 if k[0] == t[0] and t[1] in k[1]:
...                     s_id = v
...         if s_id is None:
...             return t[0]
...         return s_id
...
...     @classmethod
...     def state_factory(cls, c, n, e):
...         return getattr(cls, n)(c,n,e)
...
...     @staticmethod
...     def op_nd1(c, s, e):
...         if e is not None:
...             c['op_nd1'] = int(e)
...         while True:
...             display(c['op_nd1'])
...             c, _, e = yield (c, [s], e)
...             c['op_nd1'] = c['op_nd1']*10 + int(e)
...
...     @staticmethod
...     def op_nd2(c, s, e):
...         c['op_nd2'] = int(e)
...         while True:
...             display(c['op_nd2'])
...             c, _, e = yield (c, [s], e)
...             c['op_nd2'] = c['op_nd2']*10 + int(e)
...
...     @staticmethod
...     def op_tor(c, s, e):
...         while True:
...             if c['op_tor'] is not None:
...                 c['op_nd1'] = c['op_tor'](c['op_nd1'], c['op_nd2'])
...                 display(c['op_nd1'])
...             display(e)
...             if e == '+':
...                 c['op_tor'] = operator.add
...             elif e == '-':
...                 c['op_tor'] = operator.sub
...             elif e == '/':
...                 c['op_tor'] = operator.div
...             elif e == '*':
...                 c['op_tor'] = operator.mul
...             else:
...                 raise StopIteration
...             c, _, e = yield (c, [s], e)
...
...     @staticmethod
...     def result(c, s, e):
...         c['op_nd1'] = c['op_tor'](c['op_nd1'], c['op_nd2'])
...         c['op_tor'] = None
...         while True:
...             display(c['op_nd1'])
...             c, _, e = yield (c, [s], e)
...
...
>>> class PocketCalcOuterSM(object):
...
...     tt = {
...         (None, None): 'off',
...         ('off', 'p-on'): 'reset',
...         ('on', 'p-on'): 'reset',
...         ('reset', None): 'on',
...         ('on', 'p-off'): 'off',
...     }
...
...     @classmethod
...     def transition(cls, c, t):
...         return cls.tt.get(t, t[0])
...
...     @classmethod
...     def state_factory(cls, c, n, e):
...         if n == 'on':
...             return state_machine_from_class(PocketCalcInnerSM)(c,n,e)
...         return getattr(cls, n)(c,n,e)
...
...     @staticmethod
...     def off(c, s, e):
...         while True:
...             c, _, e = yield (c, [s], e)
...
...     @staticmethod
...     def reset(c, s, e):
...         c['op_nd1'] = 0
...         c['op_nd2'] = 0
...         c['op_tor'] = None
...         return
...         # yield statement is necessary to make this a generator
...         c, _, e = yield (c, [s], e)
...
>>> ctx = dict()
>>> pc_sm = state_machine_from_class(PocketCalcOuterSM)(ctx)
>>> e = ['p-on', '2', '+', '3', '=', '-', '1', '=', 'p-on', 'p-off']
>>> l = [val for val in iter_sm(pc_sm, iter(e))]
 0 2 + 3 5 - 1 4 0
>>> e = ['p-on', '2', '*', '3', '/', '2', '+', '1', '3', '=', 'p-off']
>>> l = [val for val in iter_sm(pc_sm, iter(e), val = l[-1])]
 0 2 * 3 6 / 2 3 + 1 13 16
"""


import unittest
import doctest


def state_machine(state_factory, transition_func):
    """Return a state machine generator function."""
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
                        ctx, s_id_vec, evt = state.next()
                    else:
                        ctx, s_id_vec, evt = state.send((ctx, state_id, evt))
                except StopIteration:
                    evt = None
                    continue
                ctx, _, evt = yield (ctx, s_id_vec + [state_id], evt)
                if state_id is None:
                    break
        finally:
            if state is not None:
                state.close()
    return sm


def state_machine_from_class(cls):
    """Create a state machine from a class.

    Creates a state machine from a class that encapsulates the state
    factory and state transition functions declared respectively as
    `state_factory` and `transition` static methods.

    """
    return state_machine(cls.state_factory, cls.transition)


def run_sm(sm, callback=None, val=None):
    """Run state machine to completion.

    The state machine passed as first parameter is run (to completion
    unless the optional callback raises StopIteration). An optional initial
    value can be passed to the state machine (defaults to None) and the
    function returns the last value returned by the state machine.

    Storing the value returned by the function and passing it to the next
    invokation of the function allows to resume execution of a state
    machine that was halted by the optional callback (by raising
    StopIteration)

    The callback function receives the state machine and last returned
    value as parameters and must return a value that will be passed to
    the next round of the state machine execution.

    """
    try:
        while True:
            val = sm.send(val)
            if callback:
                val = callback(sm, val)
    except StopIteration:
        pass
    return val


def iter_sm(sm, evt_iter=None, callback=None, val=None):
    """Return iterator for a state machine.

    The iterator returned by this function consumes an event from the
    `evt_iter` iterator and feeds it into the state machine for each
    iteration.

    The optional callback parameter is called for each iteration and can
    modify the value passed into the next round of the state machine
    execution. Execution can be halted by the callback by raising
    StopIteration.

    An optional initial value can be passed to the state machine
    (defaults to None) and can be used to resume execution of a state
    machine that was previously halted by the callback or stopped because
    the `evt_iter` iterator was exhausted.

    """
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
