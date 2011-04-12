import filecmp
import os


class DuplicateSet(object):

    class NotReallyADuplicateError(Exception):
        """Raised if duplicates added to a set are not duplicates"""

    def __init__(self):
        self.items = []
        self.size = None
        self.num_files = None
        self.messages = []

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
        """
        Output a duplicate set in human readable format that can also
        be processed when using -i.
        """
        def human_readable(number):
            """Insert dots into numbers at every three digits."""
            res = ''
            for i,c in enumerate(reversed(str(number))):
                if i and not i % 3:
                    res = '.' + res
                res = c + res
            return res
        if self.num_files:
            digest = self.items[0].digest
        else:
            digest = 'empty folders'

        s = ['', '#duplicate [%s] %s bytes %s files' % (digest, human_readable(self.size), self.num_files)]

        for d in self.items:
            s.append('keep "%s"' % d.path)
        s.append('#/duplicate [%s]' % digest)
        s.extend(self.messages)
        return '\n'.join(s)

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
            self.messages.append('-->only one item in this duplicate set, nothing to compare')
            return False
        else:
            all_good = True
            for item_idx in range(len(self.items)-1):
                for file_idx in range(len(self.items[item_idx].files)):
                    left = self.items[item_idx]
                    right = self.items[item_idx+1]
                    a = os.path.join(left.path, left.files[file_idx])
                    b = os.path.join(right.path, right.files[file_idx])

                    if not filecmp.cmp(a, b, shallow=False):
                        self.messages.append('file mismatch: %s %s' (a, b))
                        all_good = False
            if all_good:
                self.messages.append('-->identical duplicates verified')
            else:
                self.messages.append('-->WARNING: differences detected!!')
            return all_good
