# Copyright (C) 2023-2026 Paul Gauthier and Aider contributors
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import json
import traceback


def cvt(s):
    if isinstance(s, str):
        return s
    try:
        return json.dumps(s, indent=4)
    except TypeError:
        return str(s)


def dump(*vals):
    # http://docs.python.org/library/traceback.html
    stack = traceback.extract_stack()
    vars = stack[-2][3]

    # strip away the call to dump()
    vars = "(".join(vars.split("(")[1:])
    vars = ")".join(vars.split(")")[:-1])

    vals = [cvt(v) for v in vals]
    has_newline = sum(1 for v in vals if "\n" in v)
    if has_newline:
        print("%s:" % vars)
        print(", ".join(vals))
    else:
        print("%s:" % vars, ", ".join(vals))
