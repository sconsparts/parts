import contextlib
import os
import threading
import time
import unittest

import parts.part_logger as part_logger
from parts.console import Console

# Escapes rather than literals throughout: this file is *about* byte-level encoding, so it
# should not itself depend on the source file surviving an editor or a checkout intact.

# a lone 0xE2 -- the lead byte of a UTF-8 three-byte sequence with nothing following it
INVALID = b'\xe2'
# the quotes gcc puts around identifiers in diagnostics, as UTF-8 (three bytes each)
LSQUO = '\u2018'.encode()   # b'\xe2\x80\x98'
RSQUO = '\u2019'.encode()   # b'\xe2\x80\x99'
REPLACEMENT = '\ufffd'      # what errors='replace' substitutes for an undecodable byte


class stubPipe:
    '''Feeds the blocking reader a fixed sequence of readline() results, so that reads can be
    split at byte offsets a real pipe would not let us choose deterministically.'''

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.closed = False

    def readline(self):
        return self.chunks.pop(0) if self.chunks else b''

    def close(self):
        self.closed = True


class collector:
    '''Stands in for the part_logger that pipeRedirector writes to.'''

    def __init__(self):
        self.writes = []

    def WriteStream(self, taskId, streamId, msg):
        if not isinstance(msg, str):
            raise AssertionError('WriteStream received {0}, not str'.format(type(msg).__name__))
        self.writes.append(msg)

    def text(self):
        return ''.join(self.writes)


@contextlib.contextmanager
def captured_warnings():
    '''Intercept api.output.warning_msg, which otherwise needs a reporter that unit tests do
    not stand up -- and which is why the abandon branch had no coverage at all before.'''
    calls = []
    saved = part_logger.api.output.warning_msg
    part_logger.api.output.warning_msg = lambda *a, **kw: calls.append((a, kw))
    try:
        yield calls
    finally:
        part_logger.api.output.warning_msg = saved


@contextlib.contextmanager
def blocking_reader():
    """Force the win32 code path, so it stays covered when the suite runs on POSIX."""
    saved = part_logger.canPollPipes
    part_logger.canPollPipes = False
    try:
        yield
    finally:
        part_logger.canPollPipes = saved


def drain_blocking(chunks, output=None):
    '''Run the blocking (win32) reader over chunks and return (text, error).

    Driven through _readerthread rather than calling _read_blocking directly, so the platform
    dispatch and the error handling wrapped around it are covered too -- and so that asserting
    on `error` actually means something, since only _readerthread ever sets it.
    '''
    out = collector() if output is None else output
    redirector = part_logger.pipeRedirector(stubPipe(chunks), out, taskId=1,
                                            streamId=Console.out_stream)
    with blocking_reader():
        redirector._readerthread()
    text = out.text() if isinstance(out, collector) else ''
    return text, redirector.error


def feed_pipe(chunks, gap=0.15):
    '''Push chunks through a real pipe into a running pipeRedirector, with a gap between them
    so each arrives as its own os.read() -- which is how a character ends up split across
    reads in production. Closing the writer at the end gives the reader a normal EOF.'''
    read_fd, write_fd = os.pipe()
    out = collector()
    redirector = part_logger.pipeRedirector(os.fdopen(read_fd, 'rb'), out, taskId=1,
                                            streamId=Console.out_stream)
    redirector.__enter__()
    with os.fdopen(write_fd, 'wb') as writer:
        for chunk in chunks:
            writer.write(chunk)
            writer.flush()
            time.sleep(gap)
    redirector.close()
    return out.text(), redirector.error


class TestBlockingReaderDecoding(unittest.TestCase):
    '''The win32 reader. It cannot be interrupted, so on POSIX close() never has to deal with
    it -- but it still has to decode identically, so it is exercised directly here.'''

    def test_ascii_passes_through(self):
        text, error = drain_blocking([b'-- Looking for poll\n', b'-- Looking for poll - found\n'])
        self.assertEqual(error, '')
        self.assertEqual(text, '-- Looking for poll\n-- Looking for poll - found\n')

    def test_utf8_within_a_line(self):
        text, error = drain_blocking([b'error: ' + LSQUO + b'x' + RSQUO + b' undeclared\n'])
        self.assertEqual(error, '')
        self.assertEqual(text, 'error: \u2018x\u2019 undeclared\n')

    def test_invalid_byte_does_not_fail_the_task(self):
        '''An undecodable byte used to be forwarded to WriteStream as bytes, where it hit
        "chunk.msg += msg" and raised TypeError, killing the task with return code -1.'''
        text, error = drain_blocking([b'-- ok\n', b'-- bad ' + INVALID + b'\n', b'-- still going\n'])
        self.assertEqual(error, '')
        self.assertIn(REPLACEMENT, text)
        self.assertTrue(text.endswith('-- still going\n'), text)

    def test_multibyte_split_across_reads_is_stitched(self):
        text, error = drain_blocking([b'error: ' + LSQUO[:2], LSQUO[2:] + b'x here\n'])
        self.assertEqual(error, '')
        self.assertNotIn(REPLACEMENT, text)
        self.assertEqual(text, 'error: \u2018x here\n')

    def test_truncated_sequence_at_eof(self):
        text, error = drain_blocking([b'-- partial ' + LSQUO[:2]])
        self.assertEqual(error, '')
        self.assertTrue(text.startswith('-- partial '), text)
        self.assertIn(REPLACEMENT, text)

    def test_a_failing_writer_is_reported_through_readerthread(self):
        '''Gives the `error` assertions above something to be measured against: this is the
        one case on this path where error is expected to be set.'''
        class exploding:
            def WriteStream(self, taskId, streamId, msg):
                raise RuntimeError('boom')

        text, error = drain_blocking([b'-- x\n'], output=exploding())
        self.assertIn('RuntimeError', error)


class TestLineSplitting(unittest.TestCase):
    '''Lines are split by searching only each newly read chunk, on the invariant that the
    carry-over buffer never contains a newline. Searching the whole accumulated buffer on
    every read is quadratic in the length of a newline-free stream, and progress meters
    produce exactly that. The scaling itself is measured out of band; these check that the
    result is byte-exact and that the emitted granularity has not changed.'''

    def test_newline_free_stream_is_reassembled_exactly(self):
        payload = b''.join(b'\rprogress %d' % i for i in range(120000))   # ~2.5MB, no newline
        read_fd, write_fd = os.pipe()
        out = collector()
        redirector = part_logger.pipeRedirector(os.fdopen(read_fd, 'rb'), out, taskId=1,
                                                streamId=Console.out_stream)
        redirector.__enter__()
        with os.fdopen(write_fd, 'wb') as writer:
            writer.write(payload)
        redirector.close()
        self.assertEqual(redirector.error, '')
        self.assertEqual(out.text(), payload.decode())

    def test_lines_are_still_emitted_one_at_a_time(self):
        '''Several lines arriving in a single read must still reach WriteStream individually,
        or stdout/stderr interleaving in the part logs gets coarser.'''
        read_fd, write_fd = os.pipe()
        out = collector()
        redirector = part_logger.pipeRedirector(os.fdopen(read_fd, 'rb'), out, taskId=1,
                                                streamId=Console.out_stream)
        redirector.__enter__()
        with os.fdopen(write_fd, 'wb') as writer:
            writer.write(b'one\ntwo\nthree\ntail-with-no-newline')
        redirector.close()
        self.assertEqual(out.writes, ['one\n', 'two\n', 'three\n', 'tail-with-no-newline'])


class TestTimeoutOverrides(unittest.TestCase):

    def test_environment_override(self):
        os.environ['PARTS_TEST_SECONDS'] = '1.5'
        self.addCleanup(os.environ.pop, 'PARTS_TEST_SECONDS', None)
        self.assertEqual(part_logger._env_seconds('PARTS_TEST_SECONDS', 9.0), 1.5)

    def test_unset_and_unusable_values_fall_back(self):
        for bad in ('', 'soon', '0', '-3'):
            os.environ['PARTS_TEST_SECONDS'] = bad
            self.addCleanup(os.environ.pop, 'PARTS_TEST_SECONDS', None)
            self.assertEqual(part_logger._env_seconds('PARTS_TEST_SECONDS', 9.0), 9.0, bad)
        os.environ.pop('PARTS_TEST_SECONDS', None)
        self.assertEqual(part_logger._env_seconds('PARTS_TEST_SECONDS', 9.0), 9.0)


class TestInterruptibleReaderDecoding(unittest.TestCase):
    '''The POSIX reader, over a real pipe and through the reader thread.'''

    def test_lines_pass_through(self):
        text, error = feed_pipe([b'-- one\n', b'-- two\n-- three\n'])
        self.assertEqual(error, '')
        self.assertEqual(text, '-- one\n-- two\n-- three\n')

    def test_invalid_byte_becomes_a_replacement_char(self):
        text, error = feed_pipe([b'-- ok\n-- bad ' + INVALID + b'\n-- more\n'])
        self.assertEqual(error, '')
        self.assertIn(REPLACEMENT, text)
        self.assertTrue(text.endswith('-- more\n'), text)

    def test_multibyte_split_across_reads_is_stitched(self):
        '''os.read() returns whatever has arrived, so unlike readline() a real pipe can
        genuinely split a character here -- which is the production failure.'''
        text, error = feed_pipe([b'error: ' + LSQUO[:2], LSQUO[2:] + b'x here\n'])
        self.assertEqual(error, '')
        self.assertNotIn(REPLACEMENT, text)
        self.assertEqual(text, 'error: \u2018x here\n')

    def test_final_line_without_a_newline_is_flushed(self):
        text, error = feed_pipe([b'-- complete\n', b'-- no newline at end'])
        self.assertEqual(error, '')
        self.assertEqual(text, '-- complete\n-- no newline at end')


class TestPipeRedirectorShutdown(unittest.TestCase):
    '''close() has to cope with a reader that will never see EOF. That happens when a process
    spawned by the build step inherits the write end of the pipe and outlives the command:
    close_fds only covers the direct child's extra descriptors, not its descendants'. Holding
    the write end open in the test stands in for that lingering process.'''

    def make(self, output=None, join_timeout=5):
        read_fd, write_fd = os.pipe()
        self.writer = os.fdopen(write_fd, 'wb')
        self.addCleanup(self.writer.close)
        out = collector() if output is None else output
        redirector = part_logger.pipeRedirector(os.fdopen(read_fd, 'rb'), out, taskId=1,
                                                streamId=Console.out_stream)
        redirector.join_timeout = join_timeout
        return redirector, out

    def timed_close(self, redirector, limit=8):
        '''Call close() on a watchdog thread. A regression here does not make close() slow,
        it makes it never return -- so without the watchdog these tests would hang the whole
        run rather than fail, which is precisely what the bug does to a build.'''
        done = threading.Event()

        def run():
            try:
                redirector.close()
            finally:
                done.set()

        start = time.time()
        threading.Thread(target=run, daemon=True).start()
        if not done.wait(timeout=limit):
            self.fail('close() did not return within {0}s'.format(limit))
        return time.time() - start

    def test_close_returns_when_the_pipe_never_reaches_eof(self):
        redirector, out = self.make()
        redirector.__enter__()
        time.sleep(0.3)                     # let the reader settle into its poll loop
        elapsed = self.timed_close(redirector)
        self.assertLess(elapsed, 3, 'close() took {0:.1f}s'.format(elapsed))
        self.assertEqual(redirector.error, '')

    def test_output_pending_at_close_is_not_dropped(self):
        '''Stopping on the executing flag must not race ahead of text already in the pipe.'''
        redirector, out = self.make()
        redirector.__enter__()
        expected = ''.join('line {0}\n'.format(i) for i in range(500))
        self.writer.write(expected.encode())
        self.writer.flush()
        self.timed_close(redirector)        # at once: the reader may not have drained yet
        self.assertEqual(out.text(), expected)

    def test_reader_thread_is_a_daemon(self):
        redirector, out = self.make()
        self.assertTrue(redirector.thread.daemon,
                        'an abandoned reader must not keep the interpreter alive at exit')
        redirector.__enter__()
        self.timed_close(redirector)

    def test_reader_failure_is_reported_without_wedging_close(self):
        class exploding:
            def WriteStream(self, taskId, streamId, msg):
                raise RuntimeError('boom')

        redirector, out = self.make(output=exploding())
        self.writer.write(b'-- boom\n')
        self.writer.flush()
        redirector.__enter__()
        time.sleep(0.3)
        elapsed = self.timed_close(redirector)
        self.assertLess(elapsed, 3, 'close() took {0:.1f}s'.format(elapsed))
        self.assertIn('RuntimeError', redirector.error)

    def test_a_still_writing_lingerer_cannot_hold_close_open(self):
        '''The stop check only fires when the pipe goes quiet, so a leftover process that keeps
        writing would keep the reader busy until close()'s join gave up -- join_timeout per
        redirector, and part_spawner nests two of them per task. The drain is bounded instead.'''
        read_fd, write_fd = os.pipe()
        os.set_blocking(write_fd, False)        # never let the noise thread block on a full pipe
        self.addCleanup(os.close, write_fd)
        stop = threading.Event()
        self.addCleanup(stop.set)               # LIFO: runs before the fd is closed
        out = collector()
        redirector = part_logger.pipeRedirector(os.fdopen(read_fd, 'rb'), out, taskId=1,
                                                streamId=Console.out_stream)
        redirector.join_timeout = 30            # must not be what rescues us
        redirector.drain_grace = 0.5

        def chatter():
            while not stop.is_set():
                try:
                    os.write(write_fd, b'lingering process still talking\n')
                except OSError:
                    pass                        # pipe full, or closed by cleanup
                time.sleep(0.002)

        redirector.__enter__()
        threading.Thread(target=chatter, daemon=True).start()
        time.sleep(0.3)
        elapsed = self.timed_close(redirector)
        stop.set()
        self.assertLess(elapsed, 5,
                        'close() took {0:.1f}s despite a 0.5s drain grace'.format(elapsed))
        self.assertTrue(out.text(), 'nothing was captured, so it was not really draining')

    def test_pipe_is_released_even_when_it_never_reaches_eof(self):
        '''The quiet case: the reader stops on the flag and hands the pipe back.'''
        read_fd, write_fd = os.pipe()
        self.addCleanup(os.close, write_fd)
        pipein = os.fdopen(read_fd, 'rb')
        redirector = part_logger.pipeRedirector(pipein, collector(), taskId=1,
                                                streamId=Console.out_stream)
        redirector.__enter__()
        time.sleep(0.3)
        self.timed_close(redirector)
        self.assertTrue(pipein.closed, 'the reader did not release the pipe')

    def abandoning_redirector(self):
        '''Force close() to give up on a reader that is still running: a lingering writer keeps
        the pipe busy, and the drain grace deliberately outlasts the join timeout.'''
        read_fd, write_fd = os.pipe()
        os.set_blocking(write_fd, False)
        self.addCleanup(os.close, write_fd)
        stop = threading.Event()
        self.addCleanup(stop.set)               # LIFO: runs before the fd is closed
        pipein = os.fdopen(read_fd, 'rb')
        redirector = part_logger.pipeRedirector(pipein, collector(), taskId=1,
                                                streamId=Console.out_stream)
        redirector.join_timeout = 0.2
        redirector.drain_grace = 1.0

        def chatter():
            while not stop.is_set():
                try:
                    os.write(write_fd, b'still talking\n')
                except OSError:
                    pass
                time.sleep(0.002)

        redirector.__enter__()
        reader = redirector.thread              # close() clears the attribute
        threading.Thread(target=chatter, daemon=True).start()
        time.sleep(0.3)
        return redirector, pipein, stop, reader

    def test_an_abandoned_reader_releases_the_pipe(self):
        '''close() cannot close the pipe when it gives up on a live reader, so the reader has
        to hand it back itself. Otherwise every abandoned reader leaks two descriptors for the
        rest of the build.'''
        redirector, pipein, stop, reader = self.abandoning_redirector()
        with captured_warnings() as warned:
            self.timed_close(redirector)
        # the warning is the proof that close() took the abandon branch; asserting
        # thread.is_alive() out here instead would be racing the reader's own deadline
        self.assertTrue(warned, 'expected close() to warn that it abandoned the reader')
        stop.set()
        reader.join(timeout=10)
        self.assertFalse(reader.is_alive(), 'the reader never finished')
        self.assertTrue(pipein.closed, 'the abandoned reader did not release the pipe')

    def test_an_abandoned_reader_stops_writing_to_the_logger(self):
        '''part_spawner calls TaskEnd as soon as close() returns, and that deletes this task's
        cache entry. A write after that point raises KeyError with several jobs, and with one
        job goes straight to the console in the middle of an unrelated task's output.'''
        redirector, pipein, stop, reader = self.abandoning_redirector()
        out = redirector.output
        with captured_warnings() as warned:
            self.timed_close(redirector)
        self.assertTrue(warned, 'expected close() to abandon the reader')
        written = len(out.writes)
        self.assertTrue(written, 'nothing was logged before close(), so the test proves nothing')
        # the lingering writer is still going and the reader is still draining it
        time.sleep(0.4)
        self.assertTrue(reader.is_alive(), 'the reader stopped early; nothing was being drained')
        self.assertEqual(len(out.writes), written,
                         'the abandoned reader logged after close() returned')
        stop.set()
        reader.join(timeout=10)

    def test_close_is_idempotent(self):
        '''__exit__ calls close(), so an explicit close() first used to leave the second call
        dereferencing a cleared self.thread.'''
        read_fd, write_fd = os.pipe()
        with os.fdopen(write_fd, 'wb') as writer:
            writer.write(b'-- done\n')
        redirector = part_logger.pipeRedirector(os.fdopen(read_fd, 'rb'), collector(), taskId=1,
                                                streamId=Console.out_stream)
        redirector.__enter__()
        self.timed_close(redirector)
        redirector.close()                      # must not raise
        redirector.__exit__(None, None, None)   # nor via the context manager

    def test_the_abandon_warning_avoids_the_shared_stack_frame(self):
        '''warning_msg defaults to show_stack=True, which walks glb.part_frame -- module-global
        state with no lock. From a build worker thread concurrent callers can pop each other's
        entries, and an IndexError here escapes close() and masks the real build error.'''
        redirector, pipein, stop, reader = self.abandoning_redirector()
        with captured_warnings() as warned:
            self.timed_close(redirector)
        self.assertEqual(len(warned), 1)
        args, kw = warned[0]
        self.assertIs(kw.get('show_stack'), False, 'must not build a stack frame')
        self.assertIs(kw.get('print_once'), True, 'one lingering process usually means many')
        stop.set()
        reader.join(timeout=10)                 # do not leak it into the next test

    def test_pipe_is_closed_once_the_reader_has_finished(self):
        read_fd, write_fd = os.pipe()
        with os.fdopen(write_fd, 'wb') as writer:
            writer.write(b'-- done\n')      # closing the writer gives the reader its EOF
        pipein = os.fdopen(read_fd, 'rb')
        redirector = part_logger.pipeRedirector(pipein, collector(), taskId=1,
                                                streamId=Console.out_stream)
        redirector.__enter__()
        self.timed_close(redirector)
        self.assertTrue(pipein.closed)
        self.assertIsNone(redirector.thread)


class TestPipeRedirectorEndToEnd(unittest.TestCase):

    def test_invalid_bytes_over_a_real_pipe_via_the_context_manager(self):
        read_fd, write_fd = os.pipe()
        out = collector()
        with os.fdopen(write_fd, 'wb') as writer:
            writer.write(b'-- one\n-- two ' + INVALID + b'\n-- three\n')
        redirector = part_logger.pipeRedirector(os.fdopen(read_fd, 'rb'), out, taskId=1,
                                                streamId=Console.out_stream)
        redirector.__enter__()
        redirector.__exit__(None, None, None)
        self.assertEqual(redirector.error, '')
        self.assertIn(REPLACEMENT, out.text())
        self.assertTrue(out.text().endswith('-- three\n'), out.text())


class TestWriteStreamBytesGuard(unittest.TestCase):
    '''part_logger.WriteStream is reachable from part_spawner as well as the reader
    threads, so it normalizes bytes itself rather than trusting its callers.'''

    def setUp(self):
        self.flushed = []
        # bypass __init__, which needs a fully populated SCons Environment
        self.logger = part_logger.part_logger.__new__(part_logger.part_logger)
        self.logger.block_text = True
        self.logger.cache = {7: None}
        self.logger.cacheLock = threading.RLock()
        self.logger.streamWrite = {Console.out_stream: self.flushed.append,
                                   Console.error_stream: self.flushed.append}
        self.logger.otherOutWrite = {Console.out_stream: lambda taskId, msg: None,
                                     Console.error_stream: lambda taskId, msg: None}

    def test_bytes_are_normalized_before_caching(self):
        self.logger.WriteStream(7, Console.out_stream, b'-- first\n')
        self.logger.WriteStream(7, Console.out_stream, b'-- second ' + INVALID + b'\n')
        chunk = self.logger.cache[7]
        self.assertIsInstance(chunk.msg, str)
        self.assertIn(REPLACEMENT, chunk.msg)

    def test_mixed_bytes_and_str_flush_cleanly(self):
        self.logger.WriteStream(7, Console.out_stream, b'-- from the pipe\n')
        self.logger.WriteStream(7, Console.out_stream, '-- from the spawner\n')
        self.logger._empty_cache(7)
        self.assertEqual(''.join(self.flushed), '-- from the pipe\n-- from the spawner\n')


if __name__ == '__main__':
    unittest.main()
