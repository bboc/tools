
from collections import defaultdict
import hashlib
import os

import cli.app

from dirtree import DirTree


class DuplicateSet(object):

    def __init__(self, duplicates):
        self.duplicates = duplicates
        self.size = duplicates[0].size
        self.num_files = duplicates[0].num_files


    def __str__(self):
        s = '\nduplicate %s bytes %s files' % (self.size, self.num_files)
        for d in self.duplicates:
            s+='\n%s' % d.full_path
        return s


    def __cmp__(self, other):
        """neg if self < other"""


    def contains(self, other):
        """
        return True if this DuplicateSet contains the other set, e.g. if all
        folders of the other set are contained in folders of this set

        Notes:
        This can be determined by looking at paths only!!
        This set may contain more entries than the other set!!
        """



class NotReallyDuplicatesError(Exception):
    """Raised if duplicates added to a set are not duplicates"""


@cli.app.CommandLineApp
def find_duplicates(app):
    """
    Find duplicate directories in a list of given dirs.
    """
    factory = Factory()

    # build up all directory trees
    for root in app.params.root:
        print 'looking for duplicates in', root
        DirTree(root, factory)

    # build all duplicates (may still contain nested duplicates)
    dirs_by_digest = defaultdict(list)
    for item in factory.values():
        dirs_by_digest[item.digest].append(item)

    # build DuplicateSets
    duplicates = []
    for digest in dirs_by_digest:
        if len(dirs_by_digest[digest]) > 1:
            try:
                dup = DuplicateSet(dirs_by_digest[digest])

                duplicates.append(dup)
            except NotReallyDuplicatesError:
                pass

    duplicates.sort(key=lambda dup: dup.size, reverse=False)


    for d in duplicates:
        print d

    print '\n\nduplicates found:', len(duplicates)

    return 1

find_duplicates.add_param("-v", "--verbose", help="more verbose output", default=False, action="store_true")
find_duplicates.add_param("root", nargs='+', help="path(s) to search for duplicates")


class Factory(dict):
    """Factory stores all DirTrees by full_path for easy access."""
    def register(self, item):
        self[item.full_path] = item


if __name__ == '__main__':
    find_duplicates.run()

