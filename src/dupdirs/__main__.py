from __future__ import print_function
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
        duplicates = eliminate_nested_duplicates(duplicates)

    if app.params.limit_results:
        # slice the biggest few
        start = len(duplicates) - app.params.limit_results
        duplicates = duplicates[start:]


    if app.params.dircmp:
        # TODO-beb: check them with dircmp
        pass

    # show duplicates
    if app.params.verbose:
        for d in duplicates:
            print(d)

    print('\n\nduplicates found:', len(duplicates))

    return 0

find_duplicates.add_param("-v", "--verbose",
                          help="more verbose output",
                          default=False, action="store_true")

find_duplicates.add_param("-d", "--dircmp",
                          help="use dircmp to verify results (after applying the limit)",
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


def eliminate_nested_duplicates(duplicates):
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


if __name__ == '__main__':
    find_duplicates.run()

