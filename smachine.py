#!/usr/bin/env python

"""A state machine module based on generator functions

.. codeauthor:: Delio Brignoli <brignoli.delio@gmail.com>


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
    tests.addTests(doctest.DocFileSuite("README"))
    return tests

if __name__ == "__main__":
    unittest.main()
