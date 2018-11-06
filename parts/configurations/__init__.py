from __future__ import absolute_import, division, print_function

import parts.api.output
import parts.load_module as load_module


def configuration(type):
    try:
        mod = load_module.load_module(
            load_module.get_site_directories('configurations'), type, 'configtype')
    except ImportError:
        parts.api.output.error_msg('configuration "%s" was not found.' % type, show_stack=False)
