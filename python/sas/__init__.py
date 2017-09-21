#!/usr/bin/python -u
#

from __future__ import absolute_import

#
#
class SasException( Exception ) :
    def __init__( self, line = 0, msg = "SAS error", *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        self._line = line
        self._msg = msg

# simple timings
#
from contextlib import contextmanager
import time
import sys

@contextmanager
def timer( label ) :
    start = time.time()
    try :
        yield
    finally :
        end = time.time()
        sys.stdout.write( "%s: %0.3f\n" % (label,(end - start)) )

#
#
#from ply.lex import LexError
#
#
from .lexer import StarLexer
from .handlers import ErrorHandler, ContentHandlerBase, ContentHandler, ContentHandler2, SasContentHandler
from .parsebase import ParserBase
from .nmrstar import SasParser, SansParser, Parser as SansParser2
from .mmcif import CifParser
from .ddl import DdlParser
from .quickcheck import QuickChecker

# because of PLY's design I can't easily re-use lexer regexps elsewhere. so here they are again.
# (use group for warnings: "keyword group(1) in value".)
#
import re
KEYWORDS = (
    re.compile( r"(?:^|\s)(global_)\s*.*$", re.IGNORECASE ),
    re.compile( r"(?:^|\s)(data_\w+)\s*.*$", re.IGNORECASE ),
    re.compile( r"(?:^|\s)(save_[^\s]*)\s*.*$", re.IGNORECASE ),
    re.compile( r"(?:^|\s)(loop_)\s*.*$", re.IGNORECASE ),
    re.compile( r"(?:^|\s)(stop_)\s*.*$", re.IGNORECASE ),
    re.compile( r"(?:^|\s)(_\w[^\s]*)\s*.*$", re.IGNORECASE )
)

# value delimiter map: PLY token to what's passed by ``ContentHandler`` callback
#
TOKENS = {
    "CHARACTERS"   : None,
    "FRAMECODE"    : "$",
    "SINGLESTART"  : "'",
    "TSINGLESTART" : "'''",
    "DOUBLESTART"  : '"',
    "TDOUBLESTART" : '"""',
    "SEMISTART"    : ";",
    "SINGLEEND"    : "'",
    "TSINGLEEND"   : "'''",
    "DOUBLEEND"    : '"',
    "TDOUBLEEND"   : '"""',
    "SEMIEND"      : ";"
}

#
__all__ = ["TOKENS", "KEYWORDS", "SasException",
    "ContentHandlerBase", "ParserBase",
    "StarLexer",
    "ErrorHandler", "ContentHandler", "ContentHandler2", "SasContentHandler",
    "SasParser", "SansParser", "SansParser2",
    "CifParser",
    "DdlParser",
    "QuickChecker"
    ]

#
#
#
