
from collections import defaultdict
import hashlib
import os

import cli.app

from dirtree import DirTree, Factory


class DuplicateSet(object):

    class NotReallyADuplicateError(Exception):
        """Raised if duplicates added to a set are not duplicates"""


    def __init__(self):
        self.items = []
        self.size = None
        self.num_files = None


    def add(self, duplicate):
        """Add duplicate to set, check basic parameters before."""
        if not len(self.items):
            self.size = duplicate.size
            self.num_files = duplicate.num_files
        else:
            if duplicate.size != self.size:
                raise DuplicateSet.NotReallyADuplicateError()
            elif duplicate.num_files != self.num_files:
                raise DuplicateSet.NotReallyADuplicateError()
        self.items.append(duplicate)

    def __str__(self):
        s = '\nduplicate %s bytes %s files' % (self.size, self.num_files)
        for d in self.items:
            s+='\n%s' % d.path
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
        if self.size < other.size or self.num_files < other.num_files:

            return False
        for other_item in other.items:
            for item in self.items:
                if item.path.startswith(other_item.path):
                    # match found

                    print 'match', item.path, other_item.path
                    break
            else:
                return False
        return True





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
    dirs_by_digest = defaultdict(DuplicateSet)
    for item in factory.values():
        dirs_by_digest[item.digest].add(item)

    # get all actual duplicates
    duplicates = [item for item in dirs_by_digest.values() if len(item.items) > 1]
    # order duplicate sets by size
    duplicates.sort(key=lambda ds: ds.size, reverse=False)

    print '\n\nall duplicates found:', len(duplicates)

    # eliminate all nested duplicates
    real_duplicates = []
    for idx, smaller_item in enumerate(duplicates):
        for larger_item in duplicates[idx+1:]:
            if larger_item.contains(smaller_item):
                print '...contains...'
                break
        else:
            real_duplicates.append(smaller_item)


    for d in real_duplicates:
        print d

    print '\n\nreal duplicates found:', len(real_duplicates)

    return 0

find_duplicates.add_param("-v", "--verbose", help="more verbose output", default=False, action="store_true")
find_duplicates.add_param("root", nargs='+', help="path(s) to search for duplicates")




if __name__ == '__main__':
    find_duplicates.run()

