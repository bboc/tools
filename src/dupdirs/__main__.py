
from collections import defaultdict
import hashlib
import os

import cli.app

from dirtree import DirTree

@cli.app.CommandLineApp
def find_duplicates(app):
    """
    Find duplicate directories in a list of given dirs.
    """
    factory = Factory()

    for root in app.params.root:
        print 'looking for duplicates in', root
        DirTree(root, factory)

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


find_duplicates.add_param("-v", "--verbose", help="more verbose output", default=False, action="store_true")
find_duplicates.add_param("root", nargs='+', help="path(s) to search for duplicates")


class Factory(dict):
    """Factory stores all DirTrees by full_path for easy access."""
    def register(self, item):
        self[item.full_path] = item




if __name__ == '__main__':
    find_duplicates.run()

