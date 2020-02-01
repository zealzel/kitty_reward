
import json


agg_functions = {
    #  'concat': lambda x: json.dumps(format_date_series(sorted(x))),
    'list': list,
    'concat2': lambda x: json.dumps([e for e in x]),
    'join': lambda x, delimiter: delimiter.join(x),
}
