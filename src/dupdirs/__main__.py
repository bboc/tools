
from __future__ import print_function

from collections import defaultdict
import filecmp
import hashlib
import os

import cli.app

from dirtree import DirTree, Factory
from datetime import datetime

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
        def human_readable(number):
            """Insert dots into numbers at every three digits."""
            res = ''
            for i,c in enumerate(reversed(str(number))):
                if i and not i % 3:
                    res = '.' + res
                res = c + res
            return res

        s = '\nduplicate %s bytes %s files' % (human_readable(self.size), self.num_files)
        for d in self.items:
            s+='\n%s' % d.path
        return s

    def contains(self, other):
        """
        Return True if this DuplicateSet contains the other set, e.g. if all
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
                    break
            else:
                return False
        return True


    def dircmp(self):
        """Use dircmp to detect funny files in the duplicate sets"""
        if len(self.items) < 2:
            print('only one item in this duplicate set, nothing to compare')
        else:
            for idx in range(len(self.items)-1):
                dc = filecmp.dircmp(self.items[idx].path, self.items[idx+1].path)
                if dc.funny_files:
                    print('funny files:', dc.funny_files)


    def filecmp(self):
        """
        Use filecmp to realy check for identity of duplicate sets.

        Return True if identical, False otherwise
        """
        if len(self.items) < 2:
            print('only one item in this duplicate set, nothing to compare')
            return False
        else:
            for item_idx in range(len(self.items)-1):
                for file_idx in range(len(self.items[item_idx].files)):
                    left = self.items[item_idx]
                    right = self.items[item_idx+1]
                    a = os.path.join(left.path, left.files[file_idx])
                    b = os.path.join(right.path, right.files[file_idx])

                    if not filecmp.cmp(a, b, shallow=False):
                        print('file mismatch:', a, b)
                        return False
            return True


@cli.app.CommandLineApp
def find_duplicates(app):
    """
    Find duplicate directories in a list of given dirs.
    """
    start_time = datetime.now()
    factory = Factory()

    def verbose(*args):
        if app.params.verbose:
            print(*args)

    # build up all directory trees
    for root in app.params.root:
        verbose('looking for duplicates in', root)
        DirTree(root, factory, app.params.mtime, app.params.symlink_warning)

    # build all duplicates (may still contain nested duplicates)
    dirs_by_digest = defaultdict(DuplicateSet)
    for item in factory.values():
        dirs_by_digest[item.digest].add(item)

    # get all actual duplicates
    duplicates = [item for item in dirs_by_digest.values() if len(item.items) > 1]
    # order duplicate sets by size
    duplicates.sort(key=lambda ds: ds.size, reverse=False)

    if not app.params.no_nested_duplicates:
        verbose('\n\nall duplicates found:', len(duplicates))
        duplicates = _eliminate_nested_duplicates(duplicates)

    if app.params.limit_results:
        # slice the biggest few
        start = len(duplicates) - app.params.limit_results
        duplicates = duplicates[start:]

    # show results
    for d in duplicates:
        print(d)
        if app.params.dircmp:
            d.dircmp()
        if app.params.filecmp:
            if d.filecmp():
                print('-->identical duplicates verified')
            else:
                print('WARNING: differences detected!!')


    print('\n\nduplicates found:', len(duplicates))

    delta = datetime.now() - start_time
    print('time elapsed', delta)
    return 0



def _eliminate_nested_duplicates(duplicates):
    """
    This will most likely be not very effective for most data sets, so it is
    optional.
    """
    # eliminate all nested duplicates
    real_duplicates = []
    for idx, smaller_item in enumerate(duplicates):
        for larger_item in duplicates[idx+1:]:
            if larger_item.contains(smaller_item):
                break
        else:
            real_duplicates.append(smaller_item)
    return real_duplicates


find_duplicates.add_param("-v", "--verbose",
                          help="more verbose output",
                          default=False, action="store_true")

find_duplicates.add_param("-d", "--dircmp",
                          help="use dircmp to verify results (after applying the limit)",
                          default=False, action="store_true")

find_duplicates.add_param("-f", "--filecmp",
                          help="use filecmp on duplicate sets to verify results (after applying the limit)",
                          default=False, action="store_true")

find_duplicates.add_param("-s", "--symlink-warning",
                          help="warn when encountering symlinks (default behavoiur is exit on first symlink found)",
                          default=False, action="store_true")

find_duplicates.add_param("-m", "--mtime",
                          help="include last modifieds time in detection of duplicates",
                          default=False, action="store_true")

find_duplicates.add_param("-l", "--limit-results",
                          help="limit number of displayed results to n (default is all)",
                          type=int, default=0, action="store")

find_duplicates.add_param("-n", "--no-nested-duplicates", help="don't detect nested duplicates", default=False, action="store_true")
find_duplicates.add_param("-t", "--compare-tool", help="output duplicates list with compare tool", default=None, action="store")
find_duplicates.add_param("root", nargs='+', help="path(s) to search for duplicates")


if __name__ == '__main__':
    find_duplicates.run()

