# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os

from .. import DATA_PATH
from ..style import StyleSheetFile

from .matcher import matcher


__all__ = ['matcher', 'sphinx', 'sphinx_base14']


STYLESHEETS_PATH = os.path.join(DATA_PATH, 'stylesheets')

def path(filename):
    return os.path.join(STYLESHEETS_PATH, filename)


sphinx = StyleSheetFile(path('sphinx.rts'), matcher)

sphinx_base14 = StyleSheetFile(path('base14.rts'), matcher)
