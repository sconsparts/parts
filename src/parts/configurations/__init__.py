

import parts.api.output
import parts.load_module as load_module


def configuration(type):
    mod = None
    try:
        parts.api.output.verbose_msg(["configuration"],f"Trying to load configuration type: {type}")
        mod = load_module.load_module(
            load_module.get_site_directories('configurations'), type, 'configtype')
        
    except ImportError:
        pass
    
    if not mod:
        parts.api.output.error_msg(f'configuration "{type}" was not found.', show_stack=False)
