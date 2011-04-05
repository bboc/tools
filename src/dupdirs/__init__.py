"""
Find duplicate (sub)directories.

Look at:

- `dircompare <http://code.google.com/p/dircompare/>`_
- `filecmp <http://docs.python.org/library/filecmp.html>`_
- `dircmp <http://docs.python.org/library/filecmp.html#filecmp.dircmp>`_
- `cli <http://packages.python.org/pyCLI/>`_

Input directories are scanned first, and then compared.

Comparison:

- each Directory object contains a list of all files contained in the dir
  and its subdirs, ordered alphabetically
  (if equal, two subdirs are equal)
- add md5 digest for more efficient comparison

Future enhancements:
- flag to  find directories where is an extended duplicate (e.g. contains additional files)??


# TODO-beb: use commandline tools
# TODO-beb: use more than one start folders
# TODO-beb: suport for verbose
# TODO-beb: tests
# TODO-beb: replace factory by ordereddict
# TODO-beb: see if ordereddict and defaultdict can be combined
# TODO-beb: find and eliminate duplicates that are contained in othe duplicates


"""

import hashlib
import os
import cli.app
from collections import defaultdict


class DuplicateFinder(cli.app.CommandLineApp):
    """
    Find duplicate directory trees in a list of given dirs.

    To run: DuplicateFinder(options, args)()
    """
    def main(self):
        self.top = '/Users/beb/Downloads'

        self.factory = Factory()
        DirTree(self.top, self.factory)


class Factory(dict):
    """Factory stores all DirTrees by full_path for easy access."""
    def register(self, item):
        self[item.full_path] = item


class DirTree(object):
    """
    Representation of a directory.
    """
    def __init__(self, full_path, factory):
        self.full_path = full_path
        self.factory = factory
        self.factory.register(self)
        # list of child nodes
        self.children = []
        #: list of all files in this node and all children
        self.contents = []
        self.num_files = 0
        self.total_size = 0
        self._create()

    def _create(self):
        """
        load all files and subfolders, create all
        DirTrees from subfolders
        """
        # sort entries so self.contents is always sorted
        for name in sorted(os.listdir(self.full_path)):
            fp = os.path.join(self.full_path, name)
            if os.path.isfile(fp):
                s = os.stat(fp)
                # TODO-beb: maybe include st_mtime, see if that makes a difference on sample data
                self.contents.append('%s (%s)' % (name, s.st_size))
                self.num_files += 1
                self.total_size += s.st_size
            else:
                # directory
                dt = DirTree(fp, self.factory)
                self.num_files += dt.num_files
                self.total_size += dt.total_size
                for entry in dt.contents:
                    self.contents.append(os.path.join(name, entry))


    @property
    def digest(self):
        """Return or calculate md5 digest of the contents"""
        try:
            return self._digest
        except AttributeError:
            m = hashlib.md5()
            for item in self.contents:
                m.update(item)
            d = m.digest()
            self._digest = d
            return d

    def __str__(self):
        return 'size: %s\t files: %s \t%s' % (self.total_size, self.num_files, self.full_path)

if __name__ == '__main__':

    factory = Factory()
    DirTree('/Users/beb/Music/! backups to review', factory)

    #all_trees = factory.values()
    #sorted_trees = sorted(sorted_trees, keys=lambda dt:dt.digest)
    dirs_by_digest = defaultdict(list)
    for item in factory.values():
        dirs_by_digest[item.digest].append(item)
    num_dup = 0
    for digest in dirs_by_digest:
        if len(dirs_by_digest[digest]) > 1:
            num_dup+=1
            print "\nduplicate found:"
            for item in dirs_by_digest[digest]:
                print item
    print '\n\nduplicates found:', num_dup

