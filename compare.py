#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2022, Hedi Ziv @ Optalert

"""
Directory content compare tool.
"""

import argparse
import logging
from typing import Union, List
from os.path import isdir, isfile, splitext, split, join, sep

from tools import ProgressBar, Config

"""
=========
CONSTANTS
=========
"""

DESCRIPTION = \
    "Directory content compare tool."


CONFIG_VERSION = 0.1  # must specify minimal configuration file version here

DEFAULT_CFG = \
    f"# extract.py configuration file.\n" \
    f"# use # to mark comments.  Note # has to be first character in line.\n" \
    f"\n" \
    f"config_version = {CONFIG_VERSION}\n" \
    f"\n" \
    f"############################\n" \
    f"# important file locations #\n" \
    f"############################\n" \
    f"# use slash (/) or single back-slash (\\) as path separators.\n" \
    f"\n" \
    f"default_destination_path = .\n" \
    f"\n" \
    f"##########################\n" \
    f"# further configurations #\n" \
    f"##########################\n" \
    f"\n" \
    f"multiprocessing = no\n" \
    f"# multiprocessing = yes"


"""
================
GLOBAL VARIABLES
================
"""


verbose_mode = ''


"""
=========
FUNCTIONS
=========
"""


"""
========================
PATH PARSER CLASS
========================
"""


class PathParser:
    """
    Path Parsing Class.
    """

    _base_path = None

    def __init__(self) -> None:
        """
        Initialisations
        """
        _ = logging.getLogger(self.__class__.__name__)

    def __del__(self):
        """ Destructor. """
        # destructor content here if required
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def parse(self, path: str) -> str:
        assert isinstance(path, str)
        if self._base_path is None:  # not set yet
            self._base_path = sep.join(split(path)[:-1]).lstrip('/')  # assumes first time run will indicate base path
        return path[len(self._base_path) + 1:]  # skip base path as not relevant for comparison


"""
========================
COMPARER CLASS
========================
"""


class Comparer:
    """
    Argument parsing and default value population (from config).
    """

    paths = list()
    dest = ''

    def __init__(self,
                 paths: List[str],
                 dest: str) -> None:
        """
        Initialisations
        """
        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(dest, str)
        self.dest = dest

        len_paths = len(paths)
        if len_paths != 2:
            msg = f"expecting two files to compare, only received {len_paths}"
            logging.error(msg)
            raise msg

        msg = ''
        for f in paths:  # sanity check both input files
            assert isinstance(f, str)
            if isdir(f):
                msg = f'input argument {f} pointing to folder rather than file'
            elif not isfile(f):
                msg = f'invalid path argument specified {f}'
            else:
                self.paths.append(f)

        if msg != '':
            logging.error(msg)
            raise msg

    def __del__(self):
        """ Destructor. """
        # destructor content here if required
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def read_files(self, paths: List[str]) -> List[List[str]]:
        assert isinstance(paths, list)
        assert all(isinstance(x, str) for x in paths)
        assert all(isfile(x) for x in paths)

        # read files
        file_lines = list()
        p = ProgressBar('read', len(self.paths))
        for path in paths:
            with open(path) as file:
                file_content = file.readlines()
                assert isinstance(file_content, list)
                assert all(isinstance(x, str) for x in file_content)
                logging.debug(f'file {split(path)[1]} read, {len(file_content)}')
                file_lines.append(file_content)
                p.next()
        p.finish()
        return file_lines

    @staticmethod
    def does_line_start_or_end_with_strings(line: str,
                                            start_strings: Union[None, str, List[str]] = None,
                                            end_strings: Union[None, str, List[str]] = None) -> bool:
        assert isinstance(line, str)
        if start_strings is None:
            start_strings = []  # default skip checking
        if isinstance(start_strings, str):
            start_strings = [start_strings]
        assert isinstance(start_strings, list)
        assert all(isinstance(x, str) for x in start_strings)
        if end_strings is None:
            end_strings = []  # default skip checking
        if isinstance(end_strings, str):
            end_strings = [end_strings]
        assert isinstance(end_strings, list)
        assert all(isinstance(x, str) for x in end_strings)
        return any(line.startswith(x) for x in start_strings) or any(line.endswith(x) for x in end_strings)

    def parse(self, lines: List[str]) -> dict:
        assert isinstance(lines, list)
        assert all(isinstance(line, str) for line in lines)
        logging.debug('parsing file')
        folder_path = ''
        file_content = dict()
        path_parser = PathParser()  # reset base_path for each file
        for line in lines:
            line = line.rstrip()
            if self.does_line_start_or_end_with_strings(line, start_strings=['.', '/'], end_strings=':'):
                folder_path = path_parser.parse(line.rstrip('/').rstrip(':'))
                if folder_path not in file_content.keys():  # folder already found
                    file_content[folder_path] = list()  # create folder path key in file_content
            elif not self.does_line_start_or_end_with_strings(line, start_strings='total'):
                file_name = line.lstrip('/').rstrip('/').split(' ')[-1]
                file_content[folder_path].append(file_name)
        return file_content

    @staticmethod
    def find_mismatched_left(left: dict, right: dict) -> List[str]:
        assert isinstance(left, dict)
        assert isinstance(right, dict)
        mismatched = []
        progress_bar = ProgressBar('comparing', len(left) * len(right))
        for left_key in left.keys():
            for right_key in right.keys():
                if left_key.lstrip('/').lower() == right_key.lstrip('/').lower():  # case insensitive
                    left_filenames = left[left_key]
                    right_filenames = right[right_key]
                    for left_filename in left_filenames:
                        if left_filename not in right_filenames:
                            mismatched.append(f"{left_key.lstrip('/')}/{left_filename.lstrip('/')}\n")
                progress_bar.next()
        progress_bar.finish()
        logging.debug(f"found {len(mismatched)} files")
        return mismatched

    def compare(self):
        """
        Main program.
        """
        files_lines = self.read_files(self.paths)
        # parse files
        p = ProgressBar('parse', len(files_lines))
        len_files = len(files_lines)
        files_contents = list()
        for i in range(len_files):
            files_contents.append(self.parse(files_lines[i]))
            p.next()
        p.finish()
        # compare
        left_mismatched = self.find_mismatched_left(files_contents[0], files_contents[1])
        right_mismatched = self.find_mismatched_left(files_contents[1], files_contents[0])
        # write results
        p = ProgressBar('write', 2)
        with open(join(self.dest, f"missing_{splitext(split(self.paths[0])[1])[0]}.txt"), 'wt') as f:
            f.writelines(left_mismatched)
        p.next()
        with open(join(self.dest, f"missing_{splitext(split(self.paths[1])[1])[0]}.txt"), 'wt') as f:
            f.writelines(right_mismatched)
        p.finish()


"""
========================
ARGUMENT SANITY CHECKING
========================
"""


class ArgumentsAndConfigProcessing:
    """
    Argument parsing and default value population (from config).
    """

    paths = list()
    dest = ''

    def __init__(self, config_file_path: str,
                 left: str = '',
                 right: str = '',
                 dest: str = '') -> None:
        """
        Initialisations
        """
        _ = logging.getLogger(self.__class__.__name__)

        assert isinstance(config_file_path, str)
        config = Config(CONFIG_VERSION, config_file_path, DEFAULT_CFG)

        assert isinstance(dest, str)
        if dest == '':  # get default from config
            dest = config['default_destination_path']
        if isfile(dest):
            msg = f"dest argument {dest} pointing to a file rather than a folder"
            logging.error(msg)
            raise msg
        self.dest = dest

        msg = ''
        for f in (left, right):  # sanity check both input files
            assert isinstance(f, str)
            if isdir(f):
                msg = f'input argument {f} pointing to folder rather than file'
            elif not isfile(f):
                msg = f'invalid path argument specified {f}'
            else:
                self.paths.append(f)
        if msg != '':
            logging.error(msg)
            raise msg

    def __del__(self):
        """ Destructor. """
        # destructor content here if required
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def run(self):
        """
        Main program.
        """
        comparer = Comparer(self.paths, self.dest)
        comparer.compare()


"""
======================
COMMAND LINE INTERFACE
======================
"""


def main():
    """ Argument Parser and Main Class instantiation. """

    global verbose_mode

    # ---------------------------------
    # Parse arguments
    # ---------------------------------

    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter)

    no_extension_default_name = parser.prog.rsplit('.', 1)[0]
    parser.add_argument('left', nargs=1, type=str, help='left file to compare')
    parser.add_argument('right', nargs=1, type=str, help='right file to compare')
    parser.add_argument('-o', '--out', nargs=1, type=str, help='destination result file, default (not specified) '
                                                               'defined in config', default=[''])
    parser.add_argument('-c', dest='config', nargs=1, type=str, default=[f"./{no_extension_default_name}.cfg"],
                        help=f"path to config file. \"./{no_extension_default_name}.cfg\" by default")

    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-d', '--debug', help='sets verbosity to display debug level messages',
                        action="store_true")
    group1.add_argument('-v', '--verbose', help='sets verbosity to display information level messages',
                        action="store_true")
    group1.add_argument('-q', '--quiet', help='sets verbosity to display error level messages',
                        action="store_true")

    args = parser.parse_args()

    # ---------------------------------
    # Preparing LogFile formats
    # ---------------------------------

    assert isinstance(args.left, list)
    assert len(args.left) == 1
    assert isinstance(args.left[0], str)
    assert isinstance(args.right, list)
    assert len(args.right) == 1
    assert isinstance(args.right[0], str)
    assert isinstance(args.out, list)
    assert len(args.out) == 1
    assert isinstance(args.out[0], str)
    assert isinstance(args.config, list)
    assert len(args.config) == 1
    assert isinstance(args.config[0], str)

    log_filename = f'{no_extension_default_name}.log'
    try:
        logging.basicConfig(filename=log_filename, filemode='a', datefmt='%Y/%m/%d %I:%M:%S %p', level=logging.DEBUG,
                            format='%(asctime)s, %(threadName)-8s, %(name)-15s %(levelname)-8s - %(message)s')
    except PermissionError as err:
        raise PermissionError(f'Error opening log file {log_filename}. File might already be opened by another '
                              f'application. Error: {err}\n')

    console = logging.StreamHandler()
    if args.debug:
        console.setLevel(logging.DEBUG)
    elif args.verbose:
        console.setLevel(logging.INFO)
    else:  # default
        console.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(threadName)-8s, %(name)-15s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logging.getLogger('main')
    logging.info(f"Successfully opened log file named: {log_filename}")
    logging.debug(f"Program run with the following arguments: {str(args)}")

    # ---------------------------------
    # Debug mode
    # ---------------------------------

    assert isinstance(args.debug, bool)
    assert isinstance(args.verbose, bool)
    assert isinstance(args.quiet, bool)
    if args.debug:
        verbose_mode = 'debug'
    elif args.verbose:
        verbose_mode = 'verbose'
    elif args.quiet:
        verbose_mode = 'quiet'
    else:
        verbose_mode = ''

    # ---------------------------------
    # Instantiation
    # ---------------------------------

    arg_processing = ArgumentsAndConfigProcessing(config_file_path=args.config[0],
                                                  left=args.left[0],
                                                  right=args.right[0],
                                                  dest=args.out[0])
    arg_processing.run()
    logging.debug('Program execution completed. Starting clean-up.')


if __name__ == "__main__":
    main()
