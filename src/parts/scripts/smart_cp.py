import sys
import os
import stat  # needed for chmod()
import argparse
from pathlib import Path
import shutil
from collections import deque
import subprocess
from typing import List


def command_output(cmd_str):
    proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)
    # while command runs get output
    while (proc.poll() is None):
        tmp = proc.stdout.readline()
        sys.stdout.write(tmp)

    # when command is done get the rest of the output
    for last_output in proc.stdout.readlines():
        sys.stdout.write(last_output)

    # get return codes
    ret = proc.returncode
    proc.stdout.close()
    return ret


def verbose_msg(message: object, verbose: bool):
    if verbose:
        print(message)

def copytree(src: Path, dst: Path, verbose: bool):
    '''
    We use our version of copytree because one from shutil fails when destination
    directory already exists.
    '''
    dirs = deque([src])
    # copy the directory and any entries
    while dirs:
        current = dirs.popleft()
        src_dir = current
        dst_dir = dst / current.relative_to(src)

        verbose_msg(f"current={current} {current.relative_to(src)}", verbose)
        verbose_msg(f"dst={dst}", verbose)
        verbose_msg(f"dst_dir={dst_dir}", verbose)

        ############################################
        # Make sure the destination directory exists
        try:
            if not dst_dir.is_dir():
                verbose_msg(f"making dir {dst_dir}")
                os.makedirs(dst_dir)
        except OSError as error:
            if error.errno == errno.EEXIST:
                if not dst_dir.is_dir():
                    raise OSError("cannot overwrite non-directory "
                                  "'{0}' with a directory '{1}'".format(dst_dir, src_dir))
            else:
                raise
        # Iterate by source directory entries.
        # Files are copied, directories are add to the dirs list.
        for entry in src_dir.iterdir():
            verbose_msg(f"entry={entry}, dir={entry.is_dir()}, link={entry.is_symlink()}", verbose)
            if entry.is_dir() and not entry.is_symlink():
                verbose_msg(f"pushing dir {entry}", verbose)
                dirs.append(entry)
            else:
                target = dst_dir / entry.name
                verbose_msg(f"target={target}", verbose)
                if target.exists() and not os.access(target, os.W_OK):
                    st = target.stat()
                    target.chmod(stat.S_IMODE(mode.st_mode) | stat.S_IWRITE)
                    target.unlink()
                try:
                    # this might be a symlink. If it is we just recreate it
                    # This seem faster than checking if the link point to the correct value
                    if entry.is_symlink() and os.path.lexists(target):
                        verbose_msg(f"unlink {target}", verbose)
                        os.unlink(target)
                    verbose_msg(f"Copy {entry} {target.is_symlink()} to {target}", verbose)
                    shutil.copy2(entry, target, follow_symlinks=False)
                except IOError as e:
                    print(f"Error: While copying {entry} to {target}:\n {e}")
                    raise

    # all entries are added update stats on the directory
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if WindowsError and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            print(
                "Warning: CCOPY builder copying directory tree\n copystat failed for:\n  {0}\n because:\n  {1}", dst, why, show_stack=False)


def _reportError(exception: Exception, message: str, path):
    print(f"Verbose: [smart-cp] {message} for {path}: {exception}")
    # we create an exception which has the same values as came from outside but we also
    # add filename which caused the original exception
    #raise CCopyException(type(exception)(exception.errno, exception.strerror, dest))


def do_hard_copy_file(dst: Path, src: Path, verbose: bool) -> bool:
    try:
        verbose_msg(f"Creating hard link: {dst} -> {src}", verbose)
        try:
            dst.unlink(missing_ok=True)
        except TypeError:  # missing_ok may not exist in older pythons
            # till our base is new enough.. we have a fallback
            try:
                os.unlink(dst)
            except FileNotFoundError:
                pass
        try:
            dst.hardlink_to(src)
        except AttributeError:
            os.link(src, dst)
    except (OSError, IOError) as ex:
        if verbose:
            _reportError(ex, "Failed to create hard link", dst)
        return False
    return True


def do_copy_file(dst: Path, src: Path, verbose: bool) -> bool:
    try:
        # This is done because some people copy files from sources that have read only permission
        # which then can break the build

        verbose_msg(f"Copying file: {dst} -> {src}", verbose)
        shutil.copy(src, dst)
        # copy source permissions and add owner write permission
        mode = src.stat()
        dst.chmod(stat.S_IMODE(mode.st_mode) | stat.S_IWRITE)
    except (OSError, IOError) as ex:
        if verbose:
            _reportError(ex, "Failed to copy file", dst)
        return False
    return True


def make_sym_link(dst: Path, src: Path, verbose: bool) -> bool:
    '''
    Make a new symlink in dst pointing to the value the src points to
    '''
    try:# get the link that the source points to
        linkto = os.readlink(src)  # src.readlink() need py 3.9
        verbose_msg(f"Creating Symlink: {dst} -> {linkto}", verbose)
        # set the link for the new target
        dst.symlink_to(linkto)
    except (OSError, IOError) as ex:
        if verbose:
            _reportError(ex, "Failed to create symlink file", dst)
        return False
    return True


def copy_dir(dst: Path, src: Path, verbose: bool, only_copy: bool):
    verbose_msg(f"Copying directory {src} to {dst}", verbose)

    try:
        copytree(src, dst, verbose)
    except (OSError, IOError) as ex:
        if verbose:
            _reportError(ex, "Failed to create symlink file", dst)
        return False
    return True


def copy(dst_list: List[Path], src_list: List[Path], verbose: bool, only_copy: bool):
    for dst, src in zip(dst_list, src_list):
        if not src.is_symlink() and not src.exists():
            print(f"Error: {src} does not exist!")
            sys.exit(1)
        verbose_msg(f"{src} file={src.is_file()} symlink={src.is_symlink()}", verbose)
        # symlinks are always remade
        # we don't do the copy dir symlink for the build as this
        # causes a lot of more issues than it solves
        if src.is_symlink():
            if not make_sym_link(dst, src, verbose):
                # Error out
                sys.exit(2)
        elif not only_copy and src.is_file():
            # try to make hard link
            if not do_hard_copy_file(dst, src, verbose):
                # that failed, try to do a classic copy
                if not do_copy_file(dst, src, verbose):
                    # Error out
                    sys.exit(2)
        elif only_copy and src.is_file():
            # only try to do a copy
            if not do_copy_file(dst, src, verbose):
                # Error out
                sys.exit(2)
        elif src.is_dir():
            if not copy_dir(dst, src, verbose, only_copy):
                # Error out
                sys.exit(2)
        else:
            print("WTF", src, src.is_file(), src.is_dir(), src.is_symlink())
            sys.exit(3)


def _split_args(arg_str:str)->List[str]:
    '''
    faster version than shlex. Ideally the only cases we will have are path with spaces in them
    that are quoted with a "" or '' at the ends. While techincal string can be formed to break this
    simple logic here, it is unlikly (I hope). But a case like "foo"bar.txt will break this.
    This logic here is way faster then shlex for large arguments cases of the -@ argument
    '''
    split = arg_str.split()
    arg_list = []
    ln = len(split)
    print(f"split= {ln}")
    idx = 0
    while idx < ln:
        quote = None
        tok = split[idx]
        if tok.startswith('"'):
            quote = '"'
        elif tok.startswith("'"):
            quote = "'"
        if quote:
            start_idx = idx
            while not split[idx].endswith(quote):
                idx += 1
            tok = " ".join(split[start_idx:idx+1])[1:-1]
        idx += 1
        arg_list.append(tok)
    return arg_list
    
def main():
    # create parser
    parser = argparse.ArgumentParser()

    def to_bool(val):
        opt_true_values = set(['y', 'yes', 'true', 't', '1', 'on', 'all'])
        opt_false_values = set(['n', 'no', 'false', 'f', '0', 'off', 'none'])
        if val.lower() in opt_true_values:
            return True
        elif val.lower() in opt_false_values:
            return False
        else:
            print(f"Valid values are: {opt_true_values|opt_false_values}")
            raise ValueError()

    parser.add_argument("--command-file", '-@', type=Path,
                        help="File with command line options to use, for when we would have a commandline that is to long to fit")

    args, tmp = parser.parse_known_args()
    arg_str = None

    if args.command_file:

        if not args.command_file.exists():
            print(f"{args.command_file} was not found on disk!")
            sys.exit(2)
        # we have a command file. Report message if we have extra arguments
        if tmp:
            print("Usage of --command-file will cause all other command like arguments to ignored")

        cmd_file: Path = args.command_file
        arg_str = cmd_file.read_text()

    parser.add_argument("--sources", required=True, type=Path, nargs="+", help="Path to enities to copy")
    parser.add_argument("--targets", required=True, type=Path, nargs="+", help="Path with enities name to copy to")
    parser.add_argument("--copy-only", type=to_bool, default=False, help="Don't try to make a hard link, instead do a full copy.")
    parser.add_argument("--verbose", '-v', type=to_bool, default=False, help="Print extra information about copy")

    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s 1.0')

    if not arg_str:
        args = parser.parse_args()
    else:        
        arg_list = _split_args(arg_str)
        args = parser.parse_args(args=arg_list)
    if len(args.targets) != len(args.sources):
        print(
            f"Error: The number of sources and targets must be equal!\n number of:\n  sources = {len(args.sources)}\n  targets = {len(args.targets)}")
        sys.exit(1)
    
    copy(args.targets, args.sources, args.verbose, args.copy_only)


if __name__ == '__main__':
    main()
