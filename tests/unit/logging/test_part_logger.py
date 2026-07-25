import os
import threading
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
    '''Feeds pipeRedirector a fixed sequence of readline() results, so that reads can be
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


def drain(chunks):
    '''Run the reader loop synchronously over chunks; return (text, error).'''
    out = collector()
    redirector = part_logger.pipeRedirector(stubPipe(chunks), out, taskId=1, streamId=Console.out_stream)
    redirector._readerthread()
    return out.text(), redirector.error


class TestPipeRedirectorDecoding(unittest.TestCase):

    def test_ascii_passes_through(self):
        text, error = drain([b'-- Looking for poll\n', b'-- Looking for poll - found\n'])
        self.assertEqual(error, '')
        self.assertEqual(text, '-- Looking for poll\n-- Looking for poll - found\n')

    def test_utf8_within_a_line(self):
        text, error = drain([b'error: ' + LSQUO + b'x' + RSQUO + b' undeclared\n'])
        self.assertEqual(error, '')
        self.assertEqual(text, 'error: \u2018x\u2019 undeclared\n')

    def test_invalid_byte_does_not_fail_the_task(self):
        '''An undecodable byte used to be forwarded to WriteStream as bytes, where it hit
        "chunk.msg += msg" and raised TypeError, killing the task with return code -1.'''
        text, error = drain([b'-- ok\n', b'-- bad ' + INVALID + b'\n', b'-- still going\n'])
        self.assertEqual(error, '')
        self.assertIn(REPLACEMENT, text)
        self.assertTrue(text.endswith('-- still going\n'), text)

    def test_multibyte_split_across_reads_is_stitched(self):
        '''Two processes sharing the write end of the pipe can split a character across
        reads; a per-line decode() cannot recover, an incremental decoder can.'''
        text, error = drain([b'error: ' + LSQUO[:2], LSQUO[2:] + b'x here\n'])
        self.assertEqual(error, '')
        self.assertNotIn(REPLACEMENT, text)
        self.assertEqual(text, 'error: \u2018x here\n')

    def test_truncated_sequence_at_eof(self):
        text, error = drain([b'-- partial ' + LSQUO[:2]])
        self.assertEqual(error, '')
        self.assertTrue(text.startswith('-- partial '), text)
        self.assertIn(REPLACEMENT, text)

    def test_real_pipe_with_invalid_bytes(self):
        '''End to end over an actual pipe, through the reader thread and close()/join().'''
        read_fd, write_fd = os.pipe()
        out = collector()
        with os.fdopen(write_fd, 'wb') as writer:
            writer.write(b'-- one\n-- two ' + INVALID + b'\n-- three\n')
        redirector = part_logger.pipeRedirector(os.fdopen(read_fd, 'rb'), out,
                                               taskId=1, streamId=Console.out_stream)
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
