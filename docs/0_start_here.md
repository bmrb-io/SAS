# SAS
Simple API for STAR

This module contains parsers for reading main variants of STAR: mmCIF, NMR-STAR,
and the Dictionary Definition files used by both. It is also a framework/library
for writing parsers for other variants of STAR: one of the motivations behind it
was to make it easy to create parsers tailored to specific tasks and/or STAR
dialects.

I've been using python almost exclusively in the last couple of years so only
python implementation is available as of the time of this writing. The 
implementation is pure python, based on Dave Beazley's Python Lex-Yacc (PLY).
Although I currently have no plans to support other programming languages, all
python code lives in ``python`` subdirectory.

Previous iteration of this project includes parser in C++, Java, and PHP and is 
available from BMRB. Note, however, that it is not actively maintained anymore.

## STAR

Because PLY is based on python regular expressions, this code does not strictly
adhere to STAR character set definitions. For example, STAR defines whitespace
as U+0020 and U+0009 (ASCII space and tab), but we're using ``\s`` as defined
in python ``re`` module.

2012 revision of STAR format added python-style quoting of multi-line values
(triple-quotes) and a few new data types. This code supports triple-quotes
but not the new types.

Because STAR's original (1994) way of quoting multi-line values was a semicolon
as the first character on the line, newlines are important. You have to feed 
the scanner complete lines of text or it may not read semicolon-delimited
multi-line values correctly.

## Scanner

The core piece is the PLY-based scanner ``lexer.py``. The scanner is an iterable 
that returns lexical tokens, see its main section for usage examples.

The scanner can read an ``file`` object with line-based input buffering,
or you can ``send()`` it chunks of input. 

Scanner seems to be fastest when scanning one line at a time. It is not
blazing fast but scales fairly linearly with input size. Worst case scenario
is input with large number of large tables (loops).

## Parsers

Parsers for different STAR dialects are in the respective subdirectories:
``ddl``, ``mmcif``, ``nmrstar``. For NMR-STAR at least, there are several
different parsers tailored for different use patterns.

Parser classes have a main section that provides the basic usage example. 
(Familiarity with SAX parsing is recommended.)

### Writing parsers

NMR-STAR and mmCIF are restricted variants of STAR, their syntax is quite
simple. Because of that simplicity the parsers here are hand-written and 
should be fairly easy to understand. If existing ones don't do what you need,
pick one that's closest, make a copy and modify it. Consider a pull request
once you get it going.

## See also

STAR format references:

  * [DOI: 10.1021/ci00002a020](http://pubs.acs.org/doi/10.1021/ci00002a020)
  * [DOI: 10.1021/ci00019a005](http://pubs.acs.org/doi/10.1021/ci00019a005)
  * [DOI: 10.1021/ci00027a005](http://pubs.acs.org/doi/10.1021/ci00027a005)
  * [DOI: 10.1021/ci00025a009](http://pubs.acs.org/doi/10.1021/ci00025a009)
  * [DOI: 10.1021/ci300074v](http://pubs.acs.org/doi/full/10.1021/ci300074v)
  * [DOI: 10.1021/ci300076w](http://pubs.acs.org/doi/10.1021/ci300076w)

[SAX Wikipedia article](https://en.wikipedia.org/wiki/Simple_API_for_XML)

[PyNMRSTAR module](https://github.com/uwbmrb/PyNMRSTAR) on GitHub

[BMRB software page](http://www.bmrb.wisc.edu/tools/prog_corner.shtml)

[PLY](http://www.dabeaz.com/ply/ply.html)
