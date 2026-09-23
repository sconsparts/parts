'''Tests for ColorTextStream.safe_write.

safe_write() loops until the stream has accepted everything it was given. The
loop has to make progress on every path, or it does not terminate: it used to
swallow every IOError without advancing, so a write to a pipe whose reader had
gone away retried forever. Since ColorTextStream.write() holds the console lock
across the call, that took the rest of the build with it.
'''
import sys
import threading
import time
import unittest

import parts.ansi_stream as ansi_stream
from parts.ansi_stream import ColorTextStream


class FakeConsole:
    '''Only the members ColorTextStream.write() touches.'''

    def __init__(self):
        self.lock_obj = threading.Lock()
        self.clearline = False
        self.Width = 80

    def lock(self):
        self.lock_obj.acquire()

    def release(self):
        self.lock_obj.release()

    def ClearLine(self):
        pass


class RecordingStream:
    '''Records every slice offered, and accepts them per the subclass policy.'''

    #  a write attempt budget, so a stream that never makes progress fails the
    #  test instead of hanging the suite. RuntimeError is deliberately not an
    #  OSError, so safe_write cannot swallow it.
    budget = 500

    def __init__(self):
        self.offered = []

    def write(self, data):
        self.offered.append(data)
        if len(self.offered) > self.budget:
            raise RuntimeError(
                f'safe_write made no progress in {self.budget} attempts')
        return self.accept(data)

    def accept(self, data):
        return len(data)

    def flush(self):
        pass


class DeadPipe(RecordingStream):
    '''A pipe whose reader has exited. Python ignores SIGPIPE, so writes raise.'''

    def accept(self, data):
        raise BrokenPipeError(32, 'Broken pipe')


class UnbudgetedDeadPipe:
    '''A dead pipe with no attempt budget, for the console-lock test.

    The budget in RecordingStream would let the old code escape: RuntimeError is
    not an OSError, so it propagates out of write() and its finally releases the
    lock. To show the lock being held the retry has to actually be unbounded.
    The sleep keeps a regression from pinning a core for the rest of the session
    while still never terminating.
    '''

    def write(self, data):
        time.sleep(0.001)
        raise BrokenPipeError(32, 'Broken pipe')

    def flush(self):
        pass


class ClosedFile(RecordingStream):
    def accept(self, data):
        raise OSError(9, 'Bad file descriptor')


class StallsThenDrains:
    '''Blocks for a while, then starts accepting everything.

    Stands in for a reader that paused: the stream has to be usable again
    afterwards, not permanently written off.
    '''

    def __init__(self, blocked_attempts):
        self.blocked_attempts = blocked_attempts
        self.accepted = []

    def write(self, data):
        if self.blocked_attempts > 0:
            self.blocked_attempts -= 1
            err = BlockingIOError(11, 'Resource temporarily unavailable')
            err.characters_written = 0
            raise err
        self.accepted.append(data)
        return len(data)

    def flush(self):
        pass


class InterruptedOnce(RecordingStream):
    '''Raises EINTR on the first attempt, then behaves.'''

    def __init__(self):
        super().__init__()
        self.raised = False

    def accept(self, data):
        if not self.raised:
            self.raised = True
            raise InterruptedError(4, 'Interrupted system call')
        return len(data)


class DeadFlush:
    '''Accepts writes but its flush() fails, like a pipe closed between the two.'''

    def __init__(self):
        self.flushes = 0

    def write(self, data):
        return len(data)

    def flush(self):
        self.flushes += 1
        raise BrokenPipeError(32, 'Broken pipe')


class ZeroAccept(RecordingStream):
    '''Returns 0 without raising: accepted nothing, promised nothing.'''

    def accept(self, data):
        return 0


class AlwaysWouldBlock:
    '''A non-blocking stream that never drains and never accepts a character.

    No attempt budget: the point is that safe_write bounds its own wait. It waits
    with the console lock held, so an unbounded wait here is the same wedge as
    retrying a dead stream, just reached from the transient branch.
    '''

    def __init__(self):
        self.attempts = 0

    def write(self, data):
        self.attempts += 1
        err = BlockingIOError(11, 'Resource temporarily unavailable')
        err.characters_written = 0
        raise err

    def flush(self):
        pass


class PartialAccept(RecordingStream):
    def accept(self, data):
        return min(4, len(data))


class LegacyNoneReturn(RecordingStream):
    '''python2 file objects returned None from write().'''

    def accept(self, data):
        return None


class WouldBlockThenDrains(RecordingStream):
    """Reports EAGAIN a few times, taking nothing, then accepts everything.

    characters_written is 0 here. See LyingCharactersWritten for the case where
    a stream reports a non-zero one.
    """

    def __init__(self, attempts_to_block):
        super().__init__()
        self.attempts_to_block = attempts_to_block
        self.accepted = []

    def accept(self, data):
        if self.attempts_to_block > 0:
            self.attempts_to_block -= 1
            err = BlockingIOError(11, 'Resource temporarily unavailable')
            err.characters_written = 0
            raise err
        self.accepted.append(data)
        return len(data)


class LyingCharactersWritten(RecordingStream):
    """Blocks while reporting a non-zero characters_written, then accepts.

    characters_written is a *byte* count from the buffered I/O layer, not a
    character index into the string we handed over (python/cpython#83926), and a
    byte prefix can end mid-character, so there is no character position to
    resume from. The write path has to ignore it and re-offer the whole slice;
    indexing by it truncates the message and corrupts non-ASCII output.
    """

    def __init__(self, attempts_to_block):
        super().__init__()
        self.attempts_to_block = attempts_to_block
        self.accepted = []

    def accept(self, data):
        if self.attempts_to_block > 0:
            self.attempts_to_block -= 1
            err = BlockingIOError(11, 'Resource temporarily unavailable')
            # a plausible byte count: more than the characters offered, because
            # the payload is multi-byte
            err.characters_written = 7
            raise err
        self.accepted.append(data)
        return len(data)


class ClosedStream(RecordingStream):
    """A closed file object raises ValueError, which is not an OSError."""

    def accept(self, data):
        raise ValueError('I/O operation on closed file.')


class ForceFlushTarget:
    """Blocks a few times, then accepts; records flushes separately."""

    def __init__(self, attempts_to_block=0):
        self.attempts_to_block = attempts_to_block
        self.accepted = []
        self.flushes = 0

    def write(self, data):
        if self.attempts_to_block > 0:
            self.attempts_to_block -= 1
            err = BlockingIOError(11, 'again')
            err.characters_written = 0
            raise err
        self.accepted.append(data)
        return len(data)

    def flush(self):
        self.flushes += 1


def stream_for(target):
    return ColorTextStream(FakeConsole(), target)


class TestSafeWriteTerminates(unittest.TestCase):

    def test_broken_pipe_gives_up_after_one_attempt(self):
        pipe = DeadPipe()
        stream_for(pipe).safe_write('some build output\n')
        # the old code retried the same slice forever; anything above 1 means it
        # is retrying an error that cannot succeed
        self.assertEqual(len(pipe.offered), 1)

    def test_bad_descriptor_gives_up_after_one_attempt(self):
        closed = ClosedFile()
        stream_for(closed).safe_write('some build output\n')
        self.assertEqual(len(closed.offered), 1)

    def test_a_dead_stream_is_not_written_to_again(self):
        pipe = DeadPipe()
        stream = stream_for(pipe)
        for _ in range(20):
            stream.safe_write('more output\n')
        # one attempt total, not one per line: a long build must not pay a
        # failing syscall for every remaining message
        self.assertEqual(len(pipe.offered), 1)

    def test_zero_accept_does_not_loop(self):
        zero = ZeroAccept()
        stream_for(zero).safe_write('twelve chars')
        self.assertEqual(len(zero.offered), 1)

    def test_a_stream_that_never_drains_gives_up(self):
        stalled = AlwaysWouldBlock()
        stream = stream_for(stalled)
        stream.STALL_TIMEOUT = 0.05

        started = time.monotonic()
        stream.safe_write('twelve chars')
        elapsed = time.monotonic() - started

        self.assertGreater(stalled.attempts, 1, 'should have retried at least once')
        self.assertLess(elapsed, 5.0, 'safe_write did not bound its wait')


class TestStallBudgetIsPerStream(unittest.TestCase):
    '''
    The wait budget has to live on the stream, not on the call. A fresh budget
    per message means a stream that never drains costs STALL_TIMEOUT per message
    with the console lock held, which is the same wedge in slow motion.
    '''

    def test_a_second_write_to_a_stalled_stream_returns_promptly(self):
        stalled = AlwaysWouldBlock()
        stream = stream_for(stalled)
        stream.STALL_TIMEOUT = 0.2

        stream.safe_write('first message')
        attempts_after_first = stalled.attempts

        started = time.monotonic()
        stream.safe_write('second message')
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 0.1,
                        'the second message paid the stall budget again')
        # it still probes once, so the stream can come back
        self.assertGreater(stalled.attempts, attempts_after_first)

    def test_patience_is_restored_once_the_stream_drains(self):
        # a reader that paused must not be written off: after it accepts
        # something, the next stall gets the full budget again
        target = StallsThenDrains(blocked_attempts=3)
        stream = stream_for(target)
        stream.STALL_TIMEOUT = 5.0

        stream.safe_write('after the pause')
        self.assertEqual(target.accepted, ['after the pause'])

        target.blocked_attempts = 3
        stream.safe_write('and again')
        self.assertEqual(target.accepted, ['after the pause', 'and again'])


    def test_a_stalled_stream_is_waited_on_again_after_the_cooldown(self):
        # the budget must not stay expired forever, or a reader that comes back
        # is never waited for again
        target = StallsThenDrains(blocked_attempts=10_000)
        stream = stream_for(target)
        stream.STALL_TIMEOUT = 0.02
        stream.STALL_RETRY_AFTER = 0.05

        stream.safe_write('first')          # spends the budget, drops
        self.assertEqual(target.accepted, [])

        time.sleep(0.08)                    # outlast the cooldown
        target.blocked_attempts = 2         # reader came back
        stream.safe_write('second')
        self.assertEqual(target.accepted, ['second'])

    def test_a_zero_return_does_not_refresh_the_budget(self):
        # zero means the stream accepted nothing, so it is not progress. If it
        # cleared the cooldown, a stream alternating zero and EAGAIN would buy a
        # fresh STALL_TIMEOUT every round, rebuilding the delays the
        # per-instance budget exists to stop.
        class Switchable:
            def __init__(self):
                self.mode = 'block'

            def write(self, data):
                if self.mode == 'zero':
                    return 0
                err = BlockingIOError(11, 'again')
                err.characters_written = 0
                raise err

            def flush(self):
                pass

        target = Switchable()
        stream = stream_for(target)
        stream.STALL_TIMEOUT = 0.2
        stream.STALL_RETRY_AFTER = 60.0     # keep the cooldown out of the way

        stream.safe_write('spend the budget')       # expires the deadline

        target.mode = 'zero'
        stream.safe_write('accepted nothing')       # must not count as progress

        target.mode = 'block'
        started = time.monotonic()
        stream.safe_write('should be dropped fast')
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 0.1,
                        'the zero return bought a fresh stall budget')

    def test_recovery_after_the_budget_expires(self):
        # the plain case the earlier test missed: budget expires, stream then
        # accepts normally, and the next message must get through
        target = StallsThenDrains(blocked_attempts=10_000)
        stream = stream_for(target)
        stream.STALL_TIMEOUT = 0.02

        stream.safe_write('dropped')
        self.assertEqual(target.accepted, [])

        target.blocked_attempts = 0         # fully drained
        stream.safe_write('delivered')
        self.assertEqual(target.accepted, ['delivered'])


class TestForceFlushHappensOnEveryExitPath(unittest.TestCase):
    '''
    The flush used to sit inside the write loop, so it was skipped whenever the
    loop exited by a path other than the normal one, leaving progress text
    buffered with nothing to push it out.
    '''

    def test_flush_after_a_plain_write(self):
        target = ForceFlushTarget()
        stream = ColorTextStream(FakeConsole(), target)
        stream.ForceFlush = True
        stream.safe_write('hello')
        self.assertEqual(target.flushes, 1)

    def test_flush_after_the_loop_exits_via_the_exception_path(self):
        target = ForceFlushTarget(attempts_to_block=2)
        stream = ColorTextStream(FakeConsole(), target)
        stream.ForceFlush = True
        stream.safe_write('hello')
        self.assertEqual(target.accepted, ['hello'])
        self.assertEqual(target.flushes, 1)

    def test_flush_after_the_stall_budget_runs_out(self):
        # giving up on the message must not skip the flush: the buffered layer
        # may already hold part of it
        target = ForceFlushTarget(attempts_to_block=10_000)
        stream = ColorTextStream(FakeConsole(), target)
        stream.ForceFlush = True
        stream.STALL_TIMEOUT = 0.05
        stream.safe_write('hello')
        self.assertEqual(target.accepted, [])
        self.assertEqual(target.flushes, 1)

    def test_flush_after_a_zero_accept(self):
        # the loop breaks out here before ever reaching a per-iteration flush,
        # which is why the flush belongs after the loop
        target = ForceFlushTarget()
        target.write = lambda data: 0
        stream = ColorTextStream(FakeConsole(), target)
        stream.ForceFlush = True
        stream.safe_write('hello')
        self.assertEqual(target.flushes, 1)

    def test_flush_after_a_none_return(self):
        target = ForceFlushTarget()
        target.write = lambda data: None        # python2 shape
        stream = ColorTextStream(FakeConsole(), target)
        stream.ForceFlush = True
        stream.safe_write('hello')
        self.assertEqual(target.flushes, 1)


class TestInterruptedWriteIsRetried(unittest.TestCase):

    def test_eintr_is_retried_not_fatal(self):
        # InterruptedError subclasses OSError; treating it as fatal would drop
        # this message and every later one over a signal
        target = InterruptedOnce()
        stream = stream_for(target)

        stream.safe_write('interrupted once')
        self.assertEqual(len(target.offered), 2)

        # and the stream is still alive
        stream.safe_write('still working')
        self.assertEqual(target.offered[-1], 'still working')


class TestFlushIsProtected(unittest.TestCase):
    '''
    Console.flush() delegates straight to ColorTextStream.flush(), so an
    unprotected flush propagates BrokenPipeError out of an ordinary logging call
    and fails the build over a closed pipe.
    '''

    def test_flush_on_a_dead_pipe_does_not_propagate(self):
        target = DeadFlush()
        stream = ColorTextStream(FakeConsole(), target)
        stream.flush()          # must not raise
        self.assertEqual(target.flushes, 1)

    def test_flush_marks_the_stream_dead(self):
        target = DeadFlush()
        stream = ColorTextStream(FakeConsole(), target)
        stream.flush()
        stream.flush()
        # second call short circuits instead of failing again
        self.assertEqual(target.flushes, 1)

    def test_flush_retries_after_eintr_until_it_succeeds(self):
        # EINTR means the flush did not happen. Returning without retrying tells
        # the caller the stream was flushed while the final output is still
        # buffered, so it has to be retried, not deferred.
        class InterruptedFlush:
            def __init__(self, interrupts):
                self.interrupts = interrupts
                self.flushes = 0
                self.written = []

            def write(self, data):
                self.written.append(data)
                return len(data)

            def flush(self):
                self.flushes += 1
                if self.interrupts > 0:
                    self.interrupts -= 1
                    raise InterruptedError(4, 'Interrupted system call')

        target = InterruptedFlush(interrupts=2)
        stream = ColorTextStream(FakeConsole(), target)
        stream.flush()
        # two interrupted attempts plus the one that got through
        self.assertEqual(target.flushes, 3)
        # and the stream is still usable
        stream.safe_write('still alive')
        self.assertEqual(target.written, ['still alive'])

    def test_flush_gives_up_on_eintr_that_never_stops(self):
        # bounded, for the same reason the write path is: this runs under the
        # console lock
        class AlwaysInterrupted:
            def __init__(self):
                self.flushes = 0

            def write(self, data):
                return len(data)

            def flush(self):
                self.flushes += 1
                raise InterruptedError(4, 'Interrupted system call')

        target = AlwaysInterrupted()
        stream = ColorTextStream(FakeConsole(), target)
        stream.STALL_TIMEOUT = 0.05

        started = time.monotonic()
        stream.flush()
        self.assertLess(time.monotonic() - started, 5.0)
        self.assertGreater(target.flushes, 1)

    def test_a_full_buffer_defers_rather_than_retrying(self):
        # BlockingIOError is not the same case: the data is buffered and a later
        # flush pushes it, so spending the stall budget here buys nothing
        class FullBuffer:
            def __init__(self):
                self.flushes = 0

            def write(self, data):
                return len(data)

            def flush(self):
                self.flushes += 1
                raise BlockingIOError(11, 'again')

        target = FullBuffer()
        ColorTextStream(FakeConsole(), target).flush()
        self.assertEqual(target.flushes, 1)

    def test_flush_releases_the_console_lock(self):
        console = FakeConsole()
        stream = ColorTextStream(console, DeadFlush())
        stream.flush()
        self.assertTrue(console.lock_obj.acquire(timeout=5))
        console.lock_obj.release()


class TestSafeWriteDeliversData(unittest.TestCase):

    def test_whole_string_in_one_accept(self):
        target = RecordingStream()
        stream_for(target).safe_write('hello\n')
        self.assertEqual(target.offered, ['hello\n'])

    def test_partial_accepts_deliver_each_character_once(self):
        target = PartialAccept()
        stream_for(target).safe_write('twelve chars')
        # each attempt is offered the unwritten remainder, so reassembling the
        # accepted prefixes reproduces the input exactly
        delivered = ''.join(offer[:4] for offer in target.offered)
        self.assertEqual(delivered, 'twelve chars')

    def test_none_return_is_treated_as_fully_written(self):
        target = LegacyNoneReturn()
        stream_for(target).safe_write('twelve chars')
        self.assertEqual(target.offered, ['twelve chars'])

    def test_would_block_then_drains_delivers_the_whole_string_once(self):
        target = WouldBlockThenDrains(attempts_to_block=3)
        stream_for(target).safe_write('twelve chars')
        self.assertEqual(target.accepted, ['twelve chars'])

    def test_a_reported_characters_written_is_ignored(self):
        # regression guard: advancing by characters_written would hand the
        # stream a truncated slice, losing the first characters of the message
        payload = '\u2018quoted\u2019 path'
        target = LyingCharactersWritten(attempts_to_block=2)
        stream_for(target).safe_write(payload)
        self.assertEqual(target.accepted, [payload])

    def test_closed_stream_is_fatal_and_does_not_propagate(self):
        # ValueError is not an OSError, so it needs its own arm or it escapes
        # into the caller and fails the build over a logging problem
        target = ClosedStream()
        stream_for(target).safe_write('output\n')
        self.assertEqual(len(target.offered), 1)


class Recorder:
    def __init__(self):
        self.written = []

    def write(self, data):
        self.written.append(data)
        return len(data)

    def flush(self):
        pass


class TestDeadStreamNotice(unittest.TestCase):
    '''
    The notice is printed once per process. Latching the flag before the notice
    is actually delivered meant a first death that could not print it silenced
    every later one.
    '''

    def setUp(self):
        self._saved_flag = ansi_stream._reported_dead_stream
        self._saved_stderr = sys.__stderr__
        ansi_stream._reported_dead_stream = False

    def tearDown(self):
        ansi_stream._reported_dead_stream = self._saved_flag
        sys.__stderr__ = self._saved_stderr

    def test_a_death_that_cannot_report_does_not_silence_later_ones(self):
        recorder = Recorder()
        sys.__stderr__ = recorder

        # stderr itself dies: the notice has nowhere to go, so nothing is said
        ColorTextStream(FakeConsole(), recorder)._ColorTextStream__mark_dead()
        self.assertEqual(recorder.written, [])

        # a later, different stream dying must still be reported
        ColorTextStream(FakeConsole(), DeadPipe())._ColorTextStream__mark_dead()
        self.assertEqual(len(recorder.written), 1)
        self.assertIn('closed early', recorder.written[0])

    def test_the_notice_is_only_printed_once(self):
        recorder = Recorder()
        sys.__stderr__ = recorder
        for _ in range(4):
            ColorTextStream(FakeConsole(), DeadPipe())._ColorTextStream__mark_dead()
        self.assertEqual(len(recorder.written), 1)


class TestConsoleLockIsReleased(unittest.TestCase):
    '''
    write() takes the console lock and only drops it in its finally, so a
    safe_write that never returns holds the lock forever. Under a parallel build
    that stops every other thread that logs, which is how a closed pipe became a
    hung build rather than a dropped line.
    '''

    def test_write_to_dead_pipe_releases_the_console_lock(self):
        console = FakeConsole()
        stream = ColorTextStream(console, UnbudgetedDeadPipe())

        writer = threading.Thread(target=stream.write, args=('output\n',), daemon=True)
        writer.start()
        writer.join(timeout=10)

        self.assertFalse(writer.is_alive(), 'write() did not return')
        self.assertTrue(console.lock_obj.acquire(timeout=5),
                        'console lock was still held after write() returned')
        console.lock_obj.release()


if __name__ == '__main__':
    unittest.main()
