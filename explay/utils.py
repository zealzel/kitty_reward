
from collections import defaultdict
import yaml
from explay.post_func import common_funcs


def is_buildin(func_str):
    try:
        eval(func_str)
        return True
    except NameError as ex:
        return False


def replace_str(my_string, spans, replaced_words):
    cursor = 0
    new_string = ''
    for span, word in zip(spans, replaced_words):
        prev_str = my_string[cursor:span[0]]
        next_str = my_string[span[0]:span[1]]
        new_string += prev_str + str(word)
        cursor = span[1]
    new_string += my_string[cursor:]
    return new_string


def register_custom_func(name, func):
    global common_funcs
    common_funcs[name] = func


def register_func():
    import func
    funcs = [f for f in dir(func) if f.startswith('exp')]
    for func_name in funcs:
        func_name_in_yml = func_name[4:]
        register_custom_func(func_name_in_yml, getattr(func, func_name))



def to_yml(files, set_defualtdict=False, default_type=str):
    #import ipdb; ipdb.set_trace()
    content = yaml.load(open(files, 'r', encoding='utf8').read()) 
    if set_defualtdict:
        content = defaultdict(default_type, content)
    return content



#  def pd_set_option(pd, max_colwidth, max_columns, precision=1):
def pd_set_option(max_colwidth, max_columns, precision=1):
    import pandas as pd
    pd.set_option('display.expand_frame_repr', False)
    pd.set_option('display.max.colwidth', max_colwidth)
    pd.set_option('display.max_columns', max_columns)
    pd.set_option('precision', precision)
    pd.set_option('display.float_format', '{:20,.1f}'.format)
    pd.set_option('display.unicode.east_asian_width', True)



def get_local_variables(dir):
    print(globals().keys())
    var_excludes = ['In', 'Out', 'exit', 'quit']
    v = sorted(filter(lambda s:not s.startswith('_'), dir))
    v = list(filter(lambda x: x not in var_excludes, v))
    return v
