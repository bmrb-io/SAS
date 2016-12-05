#!/usr/bin/python -u
#
#
# mmCIF parsers
#
#
# mmCIF has no global blocks, there is only one data block per file.
# mmCIF is relational table format with single-row tables usually 
# formatted as lists of data items (tag - value pairs), or as loops.
# Saveframes are not allowed, all tables are in the data block.
# Nested loops are not allowed, end of loop is always implicit:
# there are no ``stop_`` markers.
#
# Legal mmCIF elements:
#  * At file level:
#    * comment
#    * start data block
#    * EOF
#  * In data block:
#    * comment
#    * start loop
#    * data item
#    * EOF
#  * In loop:
#    * comment
#    * EOF
#    * data name(s) (tags), followed by
#    * data value(s)
#    * start loop (implicit end of current loop)
#    * data item (implicit end of current loop)
#
# Incoming tokens are ``ply.LexToken( type, value, lineno, lexpos )``
#

from __future__ import absolute_import

from .parser import CifParser

__all__ = [
        "CifParser",
          ]
