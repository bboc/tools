"""
Find duplicate (sub)directories.
================================

Look at:
--------
- `dircompare <http://code.google.com/p/dircompare/>`_
- `filecmp <http://docs.python.org/library/filecmp.html>`_
- `dircmp <http://docs.python.org/library/filecmp.html#filecmp.dircmp>`_
- `cli <http://packages.python.org/pyCLI/>`_
- `python commandline tools <http://wiki.python.org/moin/CommandlineTools>`_

Notes:
------
Input directories are scanned first, and then compared.

Comparison:

- each Directory object contains a list of all files contained in the dir
  and its subdirs, ordered alphabetically
  (if equal, two subdirs are equal)
- add md5 digest for more efficient comparison

Future enhancements:
- flag to  find directories where is an extended duplicate (e.g. contains additional files)??
- launch dircompare or meld on completion??


# TODO-beb: suport for verbose
# TODO-beb: tests
# TODO-beb: replace factory by ordereddict (requires 2.7)
# TODO-beb: see if ordereddict and defaultdict can be combined (requires 2.7)
# TODO-beb: find and eliminate duplicates that are contained in othe duplicates
# TODO-beb: re-package and add #!/usr/bin/env python
"""



