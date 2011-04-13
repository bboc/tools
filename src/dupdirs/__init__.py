"""
Find duplicate (sub)directories.
================================


Notes:
------
Input directories are scanned first, and then compared.

Comparison:

- each Directory object contains a list of all files contained in the dir
  and its subdirs, ordered alphabetically
  (if equal, two subdirs are equal)
- add md5 digest for more efficient comparison
- option to use dircmd
- another option to use filecmd to compare contents of each file

Future enhancements:
- flag to  find directories where is an extended duplicate (e.g. contains additional files)??


Reference:
----------
- `dircompare <http://code.google.com/p/dircompare/>`_
- `filecmp <http://docs.python.org/library/filecmp.html>`_
- `dircmp <http://docs.python.org/library/filecmp.html#filecmp.dircmp>`_
- `cli <http://packages.python.org/pyCLI/>`_
- `python commandline tools <http://wiki.python.org/moin/CommandlineTools>`_
- `argparse <http://docs.python.org/library/argparse.html>`_


TODO-beb: tests
"""
