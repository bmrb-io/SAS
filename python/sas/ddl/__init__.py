#!/usr/bin/python -u
#
#
# Dictionary parsers
#
# DDL version of STAR is described in
#  "STAR Dictionary Definition Language: Initial Specification",
#  J. Chem. Inf. Comput. Sci. 35, 819-825 (1995).
#  DOI: 10.1021/ci00027a005
#
#  The format used by PDB and BMRB differs in that it uses saveframes
#  instead of data blocks, all "attribute tags" are different, plus
#  there's more data in there.
#
#  This format supports multiple data block per file, with
#  data block containing a mix of saveframes, loops, and data items.
#
# Legal elements:
#  * At file level:
#    * comment
#    * start data block
#    * EOF
#  * In data block:
#    * comment
#    * start saveframe
#    * start loop
#    * data item
#    * EOF
#  * In saveframe
#    * comment
#    * start loop
#    * data item
#  * In loop:
#    * comment
#    * data name(s) (tags), followed by
#    * data value(s)
#    * start loop (implicit end of current loop)
#    * data item (implicit end of current loop)
#
# Incoming tokens are ``ply.LexToken( type, value, lineno, lexpos )``
#

from __future__ import absolute_import

from .parser import Parser as DdlParser

__all__ = [
        "DdlParser",
          ]
