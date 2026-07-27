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


def drain_blocking(chunks):
    '''Run the blocking (win32) reader synchronously over chunks; return (text, error).'''
    out = collector()
    redirector = part_logger.pipeRedirector(stubPipe(chunks), out, taskId=1,
                                           streamId=Console.out_stream)
    redirector._read_blocking()
    return out.text(), redirector.error


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
