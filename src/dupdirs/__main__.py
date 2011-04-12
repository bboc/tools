
from __future__ import print_function

from collections import defaultdict
from functools import wraps
import hashlib
import sys

import cli.app

from duplicate_set import DuplicateSet, ShallowDuplicateSet
from dirtree import DirTree, Factory
from datetime import datetime


def timed(f):
    """Time execution, print results."""
    @wraps(f)
    def wrapper(*args, **kwds):
        start_time = datetime.now()

        res = f(*args, **kwds)
        delta = datetime.now() - start_time
        print('time elapsed', delta)
        return res
    return wrapper


class FindDuplicatesDirs(cli.app.CommandLineApp):

    @timed
    def main(self):
        if self.params.input:
            self.interactive()
        else:
            self.find_duplicates()


    def interactive(self):
        """Process duplicates in infile"""
        if self.params.root:
            self.error("ERROR: don't use paths in interactive mode.")
            return

        with open(self.params.input) as f:
            self._process_duplicates_from_file(f)

    def _process_duplicates_from_file(self, f):
        current_ds = None

        for line in f:
            line = line.strip()
            line_type, params = ShallowDuplicateSet.parse_line(line)
            if line_type == 'SET_START':
                print()
                print(line)
                if current_ds:
                    print('-->error: did not terminate last set properly')
                current_ds = ShallowDuplicateSet(params['num_duplicates'], params['num_files'], params['digest'], params['size'])
            elif line_type == 'SET_END':
                if current_ds.digest != params['digest']:
                    print('-->digest mismatch, ignoring')
                    continue
                current_ds.process(self.params.commit)
                # clear
                current_ds = None
            elif line_type == 'ERROR':
                current_ds.add_error(params)
            elif line_type == 'DUPLICATE':
                print(line)
                current_ds.add(params['cmd'], params['path'])


    def find_duplicates(self):
        """
        Find duplicate directories in a list of given dirs.
        """
        if not len(self.params.root):
            self.error("ERROR: please supply a path")
            return

        duplicates = self._build_duplicate_set()

        if not self.params.no_nested_duplicates:
            self.verbose('\n\nall duplicates found:', len(duplicates))
            duplicates = self._eliminate_nested_duplicates(duplicates)

        if self.params.limit_results:
            # slice the biggest few
            start = len(duplicates) - self.params.limit_results
            duplicates = duplicates[start:]

        if self.params.dircmp:
            for d in duplicates:
                d.dircmp()

        if self.params.filecmp:
            for d in duplicates:
                d.filecmp()

        # show results
        for d in duplicates:
            print(d)
        print('\n\nduplicates found:', len(duplicates))
        return 0

    def _build_duplicate_set(self):
        factory = Factory()
        # build up all directory trees
        for root in self.params.root:
            self.verbose('looking for duplicates in', root)
            DirTree(root, factory, self.params.mtime, self.params.symlink_warning)

        # build all duplicates (may still contain nested duplicates)
        dirs_by_digest = defaultdict(DuplicateSet)
        for item in factory.values():
            dirs_by_digest[item.digest].add(item)

        # get all actual duplicates
        duplicates = [item for item in dirs_by_digest.values() if len(item.items) > 1] # order duplicate sets by size
        duplicates.sort(key=lambda ds:ds.size, reverse=False)
        return duplicates

    def _eliminate_nested_duplicates(self, duplicates):
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

    def verbose(self, *args):
        if self.params.verbose:
            print(*args)

    def error(self, *args):
        """print error output"""
        print(*args, file=sys.stderr)


    def setup(self):
        """Define commandline parameters and messages."""
        super(FindDuplicatesDirs, self).setup()
        self.add_param("-v", "--verbose",
                                  help="more verbose output",
                                  default=False, action="store_true")

        self.add_param("-d", "--dircmp",
                                  help="use dircmp to verify results (after applying the limit)",
                                  default=False, action="store_true")

        self.add_param("-f", "--filecmp",
                                  help="use filecmp on duplicate sets to verify results (after applying the limit)",
                                  default=False, action="store_true")

        self.add_param("-s", "--symlink-warning",
                                  help="warn when encountering symlinks (default behavoiur is exit on first symlink found)",
                                  default=False, action="store_true")

        self.add_param("-m", "--mtime",
                                  help="include last modifieds time in detection of duplicates",
                                  default=False, action="store_true")
        self.add_param("-c", "--commit",
                                  help="actually do the deletions (only used with --input)",
                                  default=False, action="store_true")

        self.add_param("-l", "--limit-results",
                                  help="limit number of displayed results to n (default is all)",
                                  type=int, default=0, action="store")

        self.add_param("-o", "--output",
                                  help="output file for interactive deletion",
                                  action="store")

        self.add_param("-i", "--input",
                                  help="input file for interactive deletion, contents of file are processed and deleted.",
                                  action="store")

        self.add_param("-n", "--no-nested-duplicates",
                                  help="don't detect nested duplicates",
                                  default=False, action="store_true")

        self.add_param("root", nargs='*', help="path(s) to search for duplicates")


if __name__ == '__main__':
    fd =FindDuplicatesDirs()
    fd.run()

