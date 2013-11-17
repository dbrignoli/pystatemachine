
"""
Yet another `state machines with generators` module. It is intended to be a
lightweight collection of useful functions to model state machines and can be
dropped into a project's package.

I wanted something that would be easy to integrate in applications, imposing
as little as possible of the library's conventions on client code. I also
wanted an implementation that supported nesting and sequential composition
of state machines.

Why use generators? Because they are suspend-able functions, they retain
state and deal with entry/exit to/from a state without requiring an object
oriented abstraction. An application is free to use this module's functions
within classes but it does not (and should not) have to.

The state_machine_from_class() is a convenience function that returns a state
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
...         print evt, '->', state_id
...         ctx, state_id, evt = yield (ctx, state_id, evt)
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
...         # return the initial state
...         if t == (None, None):
...             return 'cool'
...         state_id, evt = t
...         # the 'test' event does not cause a state change
...         if evt == 'test':
...             return state_id
...         # pick the next state form the list
...         idx = states.index(state_id)
...         if evt == 'up':
...             idx = min(idx+1, len(states)-1)
...         else:
...             idx = max(idx-1, 0)
...         return states[idx]
...

The event_list is passed as 'context' for the state machine
>>> sm = state_machine_from_class(event_list, StateMachineClassEx1)
>>> end_state = run_sm(sm, StateMachineClassEx1.callback)
None -> cool
up -> warm
test -> warm
up -> hot
up -> hot
down -> warm
>>> end_state
([], 'warm', 'down')

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

"""

import unittest
import doctest


def state_machine(ctx, state_factory, transition_func):
    state_id, state, evt = (None, None, None)
    try:
        while True:
            next_state_id = transition_func(ctx, (state_id, evt))
            if next_state_id is None:
                break
            if (next_state_id != state_id):
                if state:
                    state.close()
                state_id = next_state_id
                state = state_factory(ctx, state_id, evt)
                ctx, state_id, evt = state.next()
            else:
                ctx, state_id, evt = state.send((ctx, state_id, evt))

            ctx, state_id, evt = yield (ctx, state_id, evt)
    finally:
        if state is not None:
            state.close()


def state_machine_from_class(ctx, cls):
    return state_machine(ctx, cls.state_factory, cls.transition)


def run_sm(sm, callback=None, val=None):
    try:
        while True:
            val = sm.send(val)
            if callback:
                val = callback(sm, val)
    except StopIteration:
        pass
    return val


class TestStateMachine_1(unittest.TestCase):

    class Context(object):
        states = None
        done = False
        transition_table = None
        evt_list = list()
        trace = list()

    @staticmethod
    def non_generator(ctx, state_id="non_generator", evt=None):
        pass

    @staticmethod
    def null_state(ctx, state_id="null_state", evt=None):
        yield ctx, state_id, None

    @staticmethod
    def example_state(ctx, state_id="example_state", evt=None):
        evt = None
        try:
            while not ctx.done:
                ctx, state_id, evt = yield (ctx, state_id, evt)
        finally:
            ctx.done = False

    @staticmethod
    def state_factory(ctx, name, evt):
        f = ctx.states[name]
        return f(ctx, name, evt)

    @staticmethod
    def transition_func(ctx, t):
        state_id, evt = t
        return ctx.transition_table.get(t, state_id)

    def cb(self, sm, val):
        ctx, state_id, evt = val
        ctx.trace.append((state_id, evt))
        if len(ctx.evt_list) > 0:
            return ctx, state_id, ctx.evt_list.pop(0)
        else:
            raise StopIteration()

    def test_nongen(self):
        ctx = TestStateMachine_1.Context()
        ctx.states = {
            'state1': self.non_generator,
        }
        ctx.transition_table = {(None, None): 'state1'}
        m = state_machine(ctx, self.state_factory, self.transition_func)
        self.assertRaises(AttributeError, m.next)

    def test_1(self):
        ctx = TestStateMachine_1.Context()
        ctx.states = {
            'state1': self.null_state,
            'state2': self.example_state,
            'state3': self.example_state,
        }
        ctx.transition_table = {
            (None, None): 'state1',
            ('state1', None): 'state2',
            ('state2', None): 'state1',
            ('state2', 'stay'): 'state2',
            ('state2', 'back'): 'state1',
            ('state2', 'next'): 'state3',
            ('state3', 'back'): 'state2',
            ('state3', 'next'): None,
        }
        ctx.evt_list = [None, None, None, 'stay']
        m = state_machine(ctx, self.state_factory, self.transition_func)
        val = run_sm(m, self.cb)
        ctx.evt_list = ['stay']
        run_sm(m, self.cb, val)
        self.assertEqual(ctx.trace, [('state1', None), ('state2', None),
                                     ('state1', None), ('state2', None),
                                     ('state2', 'stay'), ('state2', 'stay'),
                                     ('state2', 'stay')])
        ctx.trace = []
        ctx.evt_list = [None, None, None, 'stay']
        m = state_machine(ctx, self.state_factory, self.transition_func)
        val = run_sm(m, self.cb)
        ctx.done = True
        ctx.evt_list = ['stay']
        run_sm(m, self.cb, val)
        self.assertEqual(ctx.trace, [('state1', None), ('state2', None),
                                     ('state1', None), ('state2', None),
                                     ('state2', 'stay')])

        ctx.trace = []
        ctx.evt_list = [None, 'next', None, 'next']
        m = state_machine(ctx, self.state_factory, self.transition_func)
        val = run_sm(m, self.cb)
        self.assertEqual(ctx.trace, [('state1', None), ('state2', None),
                                     ('state3', None), ('state3', None)])


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite())
    return tests

if __name__ == "__main__":
    unittest.main()
