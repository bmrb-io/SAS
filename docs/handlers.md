#SAS handlers

##Differences from SAX

Most SAS callbacks return a ``stop`` flag: ``True`` to stop parsing, ``False`` to continue.
(The parser is expected to keep its current position so you can continue later from where
you stoppped.) This is a convenience feature for e.g. when you want to extract a small
subset of values from a file and don't need to waste time parsing the rest of it once you
got them.

There's three (as of the time of this writing) slightly different versions of the
``ContentHandler`` interface tailored to diferent use cases.

The callbacks themselves are of course different since STAR is not XML.

##ErrorHandler

``ErrorHandler`` defines 3 callbacks:

  * ``warning( line, message )``: this signals a possible error, for exmple a STAR keyword 
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

Common callbacks are

  * ``startGlobal( line )``: called when parser encounters ``global_``
  * ``endGlobal( line )``: not called by any parser as of this time.

Global blocks are underdefined in STAR and are not used in either mmCIF or NMR-STAR. Global
blocks have no explicit terminator so a parser will have to "fake" ``endGlobal()`` or never
trigger it.

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

###ContentHandler

###ContentHandler2
