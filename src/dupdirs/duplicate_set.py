import filecmp
import os
import re
import shutil

class DuplicateSet(object):
    """
    Duplicate set as it is built after recursively processing the file system.

    Don't use print here, aggregate all messages in self.messages.

    Output of __str__() is used in interactive mode to create a ShallowDuplicateSet
    """
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

        s = ['', '#duplicate set [%s] %s duplicates %s bytes %s files' % (digest, len(self.items), human_readable(self.size), self.num_files)]

        for d in self.items:
            s.append('[delete]("%s")' % d.path)
        s.extend(self.messages)
        s.append('#/duplicate set [%s]' % digest)
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
            self.messages.append('-->only one item in this duplicate set, nothing to compare')
        else:
            for idx in range(len(self.items)-1):
                dc = filecmp.dircmp(self.items[idx].path, self.items[idx+1].path)
                if dc.funny_files:
                    self.messages.append('-->funny files:', dc.funny_files)

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
                        self.messages.append('-->file mismatch: %s %s' (a, b))
                        all_good = False
            if all_good:
                self.messages.append('SUCCESS: identical duplicates verified')
            else:
                self.messages.append('-->WARNING: differences detected!!')
            return all_good


class ShallowDuplicateSet(object):

    line_types = [
                   ('SET_START', re.compile('\#duplicate set \[(?P<digest>[\w]{32})\] (?P<num_duplicates>[\d]*) duplicates (?P<size>[\d\.]*) bytes (?P<num_files>[\d]*) files')),
                   ('SET_END', re.compile('#/duplicate set \[(?P<digest>[\w]{32})\]')),
                   ('DUPLICATE', re.compile('\[(?P<cmd>.*)\]\(\"(?P<path>.*)\"\)')),
                   ('ERROR', re.compile('-->(?P<message>.*)')),
    ]

    @classmethod
    def parse_line(cls, line):
        """Return line_type, group_dict or None, None."""
        for name, regex in cls.line_types:
            match = regex.match(line)
            if match:
                return name, match.groupdict()
        return None, None


    def __init__(self, num_duplicates, num_files, digest, size):
        self.num_duplicates = int(num_duplicates)
        self.num_files = num_files
        self.digest = digest
        self.size = size
        self.items = []
        self.errors = []

    def add(self, cmd, folder):
        self.items.append((cmd, folder))

    def add_error(self, msg):
        self.errors.append(msg)

    def process(self, commit=False):
        """
        Process the actual deletes, do not delete anything if errors occurred.

        Err on the side of caution.
        TODO-beb: make sure all folders still exist, otherwise accidental deletion
            on rerun is possible
        """

        for _cmd, folder in self.items:
            if not os.path.exists(folder):
                print('-->ignored set: a folder does not exist')
                return
        print('processing shallow duplicate [%s]' % self.digest)
        if self.errors:
            print('-->ignored set: errors')
            return
        if self.num_duplicates != len(self.items):
            print('--> ignored set: wrong number of items', self.num_duplicates, self.items)
            return
        keep = filter(lambda x: x[0] != 'delete', self.items)
        delete = filter(lambda x: x[0] == 'delete', self.items)
        if not len(keep):
            print('-->ignored set: must keep at least one of the duplicates')
            return
        elif delete:
            for _cmd, folder in delete:
                if not commit:
                    print('dry-run: deleting', folder)
                else:
                    print('deleting', folder)
                    shutil.rmtree(folder)


