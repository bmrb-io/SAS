#!/usr/bin/python -u
#
#
# NMR-STAR parsers
#
#
# NMR-STAR does not have global blocks, there is only one data block per file,
# a data block is a collection of saveframes. Nested loops are not allowed 
# (as of NMR-STAR 3.x) and every loop ends with an explicit ``stop_`` marker.
#
# Legal NMR-STAR elements:
#  * At file level:
#    * comment
#    * start data block
#    * EOF
#  * In data block:
#    * comment
#    * start saveframe
#    * EOF
#  * In saveframe:
#    * comment
#    * data item
#    * start loop
#    * end saveframe
#  * In loop:
#    * comment
#    * data name (tag), followed by
#    * data value, followed by
#    * end loop
#
# Incoming tokens are ``ply.LexToken( type, value, lineno, lexpos )``
#

from __future__ import absolute_import

from .sansparser import SansParser
from .nvparser import Parser
from .sasparser import SasParser

__all__ = [
        "SansParser",
        "Parser",
        "SasParser"
          ]
