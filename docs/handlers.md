#SAS handlers

##Differences from SAX

Most SAS callbacks return a ``stop`` flag: ``True`` to stop parsing, ``False`` to continue.
(The parser is expected to keep its current position so you can continue later from where
you stopped.) This is a convenience feature for e.g. when you want to extract a small
subset of values from a file and don't need to waste time parsing the rest of it once you
got them.

There's three (as of the time of this writing) slightly different versions of the
``ContentHandler`` interface tailored to different use cases.

The callbacks themselves are of course different since STAR is not XML.

##ErrorHandler

``ErrorHandler`` defines 3 callbacks:

  * ``warning( line, message )``: this signals a possible error, for example a STAR keyword 
    inside a multi-line value: this may or may not be due to the value missing its closing quote.
    Return ``True`` to stop the parser or ``False`` to keep going.

  * ``error( line, message )``: this is a recoverable error, for example a loop without data. 
    Return ``True`` to stop the parser or ``False`` to keep going.

  * ``fatalError( line, message)``: this is an unrecoverable error, such as short read (premature
    EOF) or an error in the scanner. There is no return value, the parser will terminate.

##ContentHandlers

There are different versions of ``ContentHandler`` (and corresponding parsers) for different
usage patterns. The handlers define separate star/end callbacks for each STAR element, unlike
SAX's more generic ``startElement()/endElement()``. Because some STAR elements don't have an
explicit terminator, the ``end...`` callbacks may be "faked" by the parser, or not called at
all: refer to the documentation for the specific parser.

The differences are in callbacks generated for *data items* (name - value pairs) and data values.
They are listed below.

Common callbacks are

  * ``startGlobal( line )``: called when parser encounters ``global_``
  * ``endGlobal( line )``: not called by any parser as of this time.

Global blocks are not used by either mmCIF or NMR-STAR. Global blocks end at EOF so ``endGlobal()``
isn't really useful, it's here for completeness and probably will never need to be triggered.

  * ``startData( line, name )``: called when parser encounters ``data_``*name*
  * ``endData( line, name )``: STAR data blocks have no explicit terminator. NMR-STAR and
   mmCIF both use only one data block per file so this is typically called on EOF.
  * ``startSaveframe( line, name )``: called when parser encounters ``save_``*name*
  * ``endSaveframe( line, name )``: called when parser encounters ``save_``
  * ``startLoop( line )``: called when parser encounters ``loop_``
  * ``endLoop( line )``: NMR-STAR uses explicit ``stop_`` terminators for top-level loops,
   mmCIF does not. NMR-STAR parsers call this on ``stop_`` whereas mmCIF parser in this 
   package "fakes" it and calls this before the ``start...`` of the next element or ``endData()``.
  * ``comment( line, text )``: the parsers do not ignore comments, it's up to you to decide
   whether you want to keep them or not.

###SasContentHandler

This handler is the closest to SAX model. All values are returned as a sequence of ``startValue()`` -
`` characters()`` [...] - ``endValue()`` callbacks. This can be more efficient when reading files
with large multi-line values (CLOBs) as the value is returned one line at a time instead of reading
it all into a buffer and returning the whole thing at once. The downside is 3+ callbacks per value: 
if the input has a lot of small values (e.g. large coordinate tables) and overhead of subroutine 
call is significant (python), this parser becomes noticeably slower than the others.

Data items are returned as separate tag and value elements. A loop is returned as ``startLoop()``
followed by a sequence of tags, followed by a sequence of values and ``endLoop()``.

  * ``tag( line, tag )``: tag, aka *data name*.
  * ``starValue( line, delimiter )``: delimiter is null for bareword values or a character string:
    dollar sign ('$') for framecode values, single or double-quote, semicolon, or python-style 
   triple- single or double quotes.
  * ``characters( line, value )``: as with SAX, there may be multiple ``characters()`` calls per
   value. E.g. for multi-line values there will usually be one per line.
  * ``endValue( line, delimiter )``: delimiter is the same as in ``startValue()``

###ContentHandler2

Data items are returned as separate tag and value elements. A loop is returned as ``startLoop()``
followed by a sequence of tags, followed by a sequence of values and ``endLoop()``.

Data value is returned in a single callback instead of ``start() - characters() - end()`` sequence.

  * ``tag( line, tag )``: tag, aka *data name*.
  * ``value( line, value, delimiter )``: delimiter is null for bareword values or a character string:
    dollar sign ('$') for framecode values, single or double-quote, semicolon, or python-style 
    triple- single or double quotes.

###ContentHandler

All data items are returned in a single ``data`` callback: the parser buffers the tag and returns
it together with the value after that is parsed.

This can be marginally slower than ``ContentHandler2`` on files with many large loops, but on
average they are about equally fast. This is convenient for extracting values from a STAR file,
e.g. pull the residue sequence out of a data table. ``ContentHandler2``, on the other hand,
works better for tasks like database loading where you need to collect all column (tag) names
for the SQL INSERT statement first, and then run that statement for every row of input values.

Note that nested loops (multi-dimensional tables) would be difficult/impossible to fit into this 
interface so it's unsuitable for a full-fledged STAR parser. Neither mmCIF nor NMR-STAR use 
nested loops.

  * ``data( tag, tagline, value, valline, delimiter, inloop )``: tag - value pair
    * ``tag``: tag (data name),
    * ``tagline``: line where tag was found,
    * ``value``: data value,
    * ``valline``: line where value was found. For multi-line values it's one of the lines.
    * ``delimiter``: null for bareword values or a character string: dollar sign ('$') for 
      framecode values, single or double-quote, semicolon, or python-style triple- single 
      or double quotes,
    * ``inloop``: true for loop items, false for "free" items.
