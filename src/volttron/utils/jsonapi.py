# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Installable Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2022 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}

from json import dump, load, loads, dumps as json_dumps
import re
import attr
from attr import asdict
from typing import Any

__all__ = ("dump", "dumpb", "dumps", "load", "loadb", "loads", "strip_comments",
           "parse_json_config")

def attr_default(o: Any) -> Any:
    if attr.has(o.__class__):
        return asdict(o)
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

def dumps(object, **kwargs):
    if "default" not in kwargs:
        # if caller hasn't included their own default use our that handles attr data classes
        return json_dumps(object, default=attr_default, **kwargs)
    else:
        return json_dumps(object, **kwargs)

def dumpb(data, **kwargs):
    return dumps(data, **kwargs).encode("utf-8")


def loadb(s, **kwargs):
    return loads(s.decode("utf-8"), **kwargs)


_comment_re = re.compile(
    r'((["\'])(?:\\?.)*?\2)|(/\*.*?\*/)|((?:#|//).*?(?=\n|$))',
    re.MULTILINE | re.DOTALL,
)


def _repl(match):
    """Replace the matched group with an appropriate string."""
    # If the first group matched, a quoted string was matched and should
    # be returned unchanged.  Otherwise a comment was matched and the
    # empty string should be returned.
    return match.group(1) or ""


def strip_comments(string):
    """Return string with all comments stripped.
    Both JavaScript-style comments (//... and /*...*/) and hash (#...)
    comments are removed.
    """
    return _comment_re.sub(_repl, string)


def parse_json_config(config_str):
    """Parse a JSON-encoded configuration file."""
    return loads(strip_comments(config_str))