#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2022, Hedi Ziv @ Optalert

"""
tools.
"""

import logging
from datetime import datetime
from json import dump, load
from os.path import isdir, isfile, split
from typing import Union

from pandas import DataFrame, Series

"""
=========
CONSTANTS
=========
"""

CONFIG_VERSION = 0.6  # must specify minimal configuration file version here

DEFAULT_CFG = \
    f"# frp.py configuration file.\n" \
    f"# use # to mark comments.  Note # has to be first character in line.\n" \
    f"\n" \
    f"config_version = {CONFIG_VERSION}\n" \
    f"\n" \
    f"############################\n" \
    f"# important file locations #\n" \
    f"############################\n" \
    f"# use slash (/) or single back-slash (\\) as path separators.\n" \
    f"\n" \
    f"default_frp_credentials_file_path = .\\frp_OptWeb3_credentials.json\n" \
    f"default_frp_parameter_file_path = .\\frp_OptWeb3_connection_parameters.json\n" \
    f"default_frp_query_file_path = .\\get_drivers_from_site_within_date_range_query.txt\n" \
    f"default_get_site_id_query_file_path = .\\get_site_id_query.txt\n" \
    f"default_get_imeis_from_site_query_file_path = .\\get_imeis_from_site_query.txt\n" \
    f"default_destination_path = .\\test\n" \
    f"path_to_drivers_csv = .\\FRP_drivers_with_OSA_diagnosis.csv\n" \
    f"\n" \
    f"default_site = Spence\n" \
    f"# index_col = yes\n" \
    f"index_col = no"

DEFAULT_CREDENTIALS = {
    "username": "<your_username_here>",
    "password": "<your_password_here>"
}

DEFAULT_FRP_PARAMETERS = {
    "driver": "{InterSystems ODBC35}",
    "url": "192.168.1.7",
    "port": 1972,
    "database": "OPT"
}

DEFAULT_QUERY = \
    "select\n" \
    "    Driver as Driver_ID,\n{}" \
    "    Site->Name as SiteName,\n" \
    "    VehicleSystemEvent->Reason,\n{}" \
    "    Vehicle->AssetNo,\n" \
    "    eventdatetime,\n" \
    "    summarystat\n" \
    "from OPT_DATA.SummaryStat\n" \
    "where{}\n" \
    "    eventdatetime > '{}' and eventdatetime <= '{}'"

"""
================
GLOBAL VARIALBES
================
"""


"""
=========
FUNCTIONS
=========
"""


def is_number(string_value: str) -> bool:
    assert isinstance(string_value, str)
    try:
        float(string_value)
        return True
    except ValueError:
        return False


def read_txt_file(path_to_file: str) -> Union[None, str]:
    assert isinstance(path_to_file, str)
    content = None
    if isfile(path_to_file):
        with open(path_to_file, 'rt') as txt_file:
            content = txt_file.read()
        # validate content
        if not isinstance(content, str):
            logging.error(f"invalid content in file {split(path_to_file)[1]}")
    return content


def write_txt_file(path_to_file: str, content: Union[None, str]):
    assert isinstance(path_to_file, str)
    if content is not None:
        assert isinstance(content, str)
        with open(path_to_file, 'tw') as file:
            file.write(content)
            logging.debug(f"{split(path_to_file)[1]} file written")


def read_json_file(path_to_file: str) -> Union[None, dict]:
    assert isinstance(path_to_file, str)
    content = None
    if isfile(path_to_file):
        with open(path_to_file) as credentials_file:
            content = load(credentials_file)
        # validate content
        if not isinstance(content, dict):
            logging.error(f"invalid content in file {split(path_to_file)[1]}")
    return content


def write_json_file(path_to_file: str, content: Union[None, dict]):
    assert isinstance(path_to_file, str)
    if content is not None:
        assert isinstance(content, dict)
        with open(path_to_file, 'w') as file:
            dump(content, file)
            logging.debug(f"{split(path_to_file)[1]} file written")


def convert_vehicle_did_to_imei(vehicle_system_did: str) -> int:
    assert isinstance(vehicle_system_did, str)
    return int(vehicle_system_did.replace('A', '').replace('-', ''))


def format_date_field_for_rms(time_field: datetime) -> str:
    assert isinstance(time_field, datetime)
    return time_field.strftime("%Y%m%d%H%M%S")


def apply_function_to_column(df: DataFrame, col: str, func) -> Series:
    assert isinstance(df, DataFrame)
    assert isinstance(col, str)
    assert col in df.columns
    return df.loc[:, col].apply(func)


def read_file(path_to_file: str, default_content: Union[None, str, dict],
              file_reader_function, file_writer_function,
              expected_extension: str = 'txt',
              always_generate_new_file: bool = False) -> Union[None, str, dict]:
    assert isinstance(path_to_file, str)
    if default_content is not None:
        assert isinstance(default_content, (str, dict))
    content = default_content
    assert isinstance(expected_extension, str)
    expected_extension = expected_extension.lower()
    assert isinstance(always_generate_new_file, bool)
    if isdir(path_to_file):
        logging.error(f"path {path_to_file} should point to a file, not a directory")
    elif always_generate_new_file or not isfile(path_to_file):  # file doesn't exist, try to write default content
        if default_content is not None:
            file_writer_function(path_to_file, default_content)
            logging.info(f"{path_to_file} does not exist, writing default content")
        else:
            logging.error(f"path {path_to_file} not pointing to valid file")
    else:  # file exists
        if not path_to_file.lower().endswith(expected_extension):
            logging.warning(f"{split(path_to_file)[1]} file extension expected to be .{expected_extension}")
        else:
            content = file_reader_function(path_to_file)  # read file
    return content


def read_parameter_file(path_to_file: str,
                        default_content: Union[None, dict],
                        always_generate_new_file: bool = False) -> Union[None, dict]:
    return read_file(path_to_file, default_content, read_json_file, write_json_file, "json", always_generate_new_file)


def read_query_file(path_to_file: str,
                    default_content: Union[None, str] = None,
                    always_generate_new_file: bool = False) -> Union[None, str]:
    return read_file(path_to_file, default_content, read_txt_file, write_txt_file, "txt", always_generate_new_file)


"""
==================
CONFIG FILE PARSER
==================
"""


class Config:
    """
    Configuration file parser.
    Note all return values in string format.
    """

    _config = {}

    def __init__(self, config_version: float, path: Union[None, str] = None, default_cfg: str = DEFAULT_CFG):
        """
        Initialisations
        @param path: Path to config file.  Local directory by default
        @param config_version: must specify minimum config file version here
        @param default_cfg: Default CFG
        """

        self.log = logging.getLogger(self.__class__.__name__)
        assert isinstance(config_version, float)
        assert isinstance(default_cfg, str)
        if path is None:
            path = f'./{self.__class__.__name__}.cfg'
            logging.debug(f'Path to configuration file not specified.  Using: {path}')
        else:
            assert isinstance(path, str)
            if isfile(path):
                logging.debug(f'Configuration file detected as {path}')
            else:
                logging.debug(f"Configuration file path specified {path} does not exist, creating default")
                try:
                    with open(path, 'wt') as config_file:
                        config_file.write(default_cfg)
                    config_file.close()
                    logging.debug(f'{path} file created')
                except PermissionError as e:
                    logging.error(f"can not access file {path}. Might be opened by another application. "
                                  f"Error returned: {e}")
                    raise PermissionError(f"can not access file {path}. Might be opened by another application."
                                          f"Error returned: {e}")
                except OSError as e:
                    logging.error(f"can not access file {path}. Might be opened by another application. "
                                  f"Error returned: {e}")
                    raise OSError(f"can not access file {path}. Might be opened by another application."
                                  f"Error returned: {e}")
                except UserWarning as e:
                    logging.debug(f"{path} file empty - {e}")
                    raise UserWarning(f"can not access file {path}. Might be opened by another application. "
                                      f"Error returned: {e}")
        # read file
        try:
            with open(path, 'rt') as config_file:
                for line in config_file:
                    # skip comment or empty lines
                    if not (line.startswith('#') or line.startswith('\n')):
                        var_name, var_value = line.split('=')
                        var_name = var_name.strip(' \t\n\r')
                        var_value = var_value.strip(' \t\n\r')
                        if ',' in var_value:
                            self._config[var_name] = [x.strip(' \t\n\r') for x in var_value.split(',')]
                        else:
                            self._config[var_name] = var_value
            config_file.close()
            logging.info(f'Configuration file {path} read.')
            logging.debug('Config file contents:')
            # log config file content
            for key in self._config.keys():
                logging.debug(f"config[{key}] = {self._config[key]}")
            logging.debug('End of Config file content.')
        except PermissionError as e:
            logging.error(f"can not access file {path}. Might be opened by another application. "
                          f"Error returned: {e}")
            raise PermissionError(f"can not access file {path}. Might be opened by another application."
                                  f"Error returned: {e}")
        except OSError as e:
            logging.error(f"can not access file {path}. Might be opened by another application. "
                          f"Error returned: {e}")
            raise OSError(f"can not access file {path}. Might be opened by another application."
                          f"Error returned: {e}")
        except UserWarning as e:
            logging.debug(f"{path} file empty - {e}")
            raise UserWarning(f"can not access file {path}. Might be opened by another application. "
                              f"Error returned: {e}")
        # verify config_version
        file_version = self.__getitem__("config_version")
        fault_msg = f"Config file {split(path)[1]} version ({file_version}) is lower than " \
                    f"expected {config_version}. Consider deleting and re-run code to " \
                    f"generate default config file "\
                    f"with latest version."
        try:
            file_version = float(file_version)
        except ValueError as e:
            logging.error(f"config_version value in file is not a valid float. error: {e}")
        if not isinstance(file_version, (float, int)):
            raise ValueError(fault_msg)
        if file_version < config_version:
            raise ValueError(fault_msg)

    def __del__(self):
        """ Destructor. """

        # destructor content here if required
        logging.debug(f'{str(self.__class__.__name__)} destructor completed.')

    def __getitem__(self, item: str) -> Union[str, list]:
        """
        return parameter from configuration file
        @param item: name of parameter
        @return: value of parameter from configuration file
        """
        assert isinstance(item, str)
        if item in self._config:
            try:
                ret = self._config[item]
            except KeyError as e:
                logging.error(f'parameter requested {item} not in config file, error: {e}')
                return ''
            if isinstance(ret, str) and ret.lower() == 'none':
                ret = None
            return ret
        else:
            logging.info(f'parameter requested {item} not in config file')
            return ''


"""
==================
PROGRESS BAR CLASS
==================
"""


class ProgressBar:
    """ Parse arguments. """

    # class globals
    _title_width = 25
    _width = 32
    _bar_prefix = ' |'
    _bar_suffix = '| '
    _empty_fill = ' '
    _fill = '#'
    progress_before_next = 0
    debug = False
    verbose = False
    quiet = False

    _progress = 0  # between 0 and _width -- used as filled portion of progress bar
    _increment = 0  # between 0 and (_max - _min) -- used for X/Y indication right of progress bar

    def __init__(self, text, maximum=10, minimum=0, verbosity_mode=''):
        """ Initialising parsing arguments.
        @param text: title of progress bar, displayed left of the progress bar
        @type text: str
        @param maximum: maximal value presented by 100% of progress bar
        @type maximum: int
        @param minimum: minimal value, zero by default
        @type minimum: int
        @param verbosity_mode: 'debug', 'verbose' or 'quiet'
        @type verbosity_mode: str
        """

        self.log = logging.getLogger(self.__class__.__name__)
        assert isinstance(text, str)
        assert isinstance(maximum, int)
        assert isinstance(minimum, int)
        assert maximum > minimum
        self._text = text
        self._min = minimum
        self._max = maximum
        self._progress = 0
        self._increment = 0
        # LOGGING PARAMETERS
        assert isinstance(verbosity_mode, str)
        assert verbosity_mode in ['', 'debug', 'verbose', 'quiet']
        if verbosity_mode == 'debug':
            self.debug = True
        elif verbosity_mode == 'verbose':
            self.verbose = True
        elif verbosity_mode == 'quiet':
            self.quiet = True
        logging.debug('{} progress bar started'.format(self._text))
        self.update()

    def __del__(self):
        """ Destructor. """

        # destructor content here if required
        logging.debug('{} destructor completed.'.format(str(self.__class__.__name__)))

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        """
        Set length of the progress bar in characters.
        @param value: number of characters
        @type value: int
        """
        assert isinstance(value, int)
        assert 0 < value < 80
        self._width = value

    @property
    def title_width(self):
        return self._title_width

    @title_width.setter
    def title_width(self, value):
        """
        Set padding width for text before the progress bar.
        @param value: padding width in number of characters
        @type value: int
        """
        assert isinstance(value, int)
        assert 0 < value < 80
        self._title_width = value

    def next(self, n=1):
        """ Increment progress bar state.
        @param n: increment progress bar by n
        @type n: int
        """

        assert isinstance(n, int)
        assert n >= 0
        if n > 0:
            self._progress += 1 / (n * (self._max - self._min) / self._width)
            if self._progress > self._width:
                self._progress = self._width
            self._increment += n
            if float(self._progress) >= self.progress_before_next + 1 / self._width:
                self.progress_before_next = self._progress
                self.update()

    def update(self, end_char='\r'):
        """ Update progress bar on console.
        @param end_char: character used to command cursor to get back to beginning of line without carriage return.
        @type end_char: str
        """

        assert isinstance(end_char, str)
        diff = self._max - self._min
        bar = self._fill * int(self._progress)
        empty = self._empty_fill * (self._width - int(self._progress))
        if not self.debug and not self.verbose and not self.quiet:
            print("{:<{}.{}s}{}{}{}{}{}/{}".format(self._text, self._title_width, self._title_width,
                                                   self._bar_prefix, bar, empty, self._bar_suffix,
                                                   str(self._increment), str(diff)), end=end_char)

    def finish(self):
        """ Clean up and release handles. """

        self._progress = self._width
        self._increment = self._max - self._min
        if self._increment < 0:
            self._increment = 0
        self.update('\n')
        logging.debug('{} finished'.format(self._text))
