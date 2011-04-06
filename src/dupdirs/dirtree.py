import hashlib
import os


class DirTree(object):
    """
    Representation of a directory.
    """
    def __init__(self, path, factory, use_mtime, symlink_warning):
        self.path = path
        self.factory = factory
        self.use_mtime = use_mtime
        self.symlink_warning = symlink_warning
        self.factory.register(self)
        # list of child nodes
        self.children = []
        #: list of all files in this node and all children
        self.contents = []
        self.num_files = 0
        self.size = 0
        self._create()

    def _create(self):
        """
        load all files and subfolders, create all
        DirTrees from subfolders
        """
        # sort entries so self.contents is always sorted
        for name in sorted(os.listdir(self.path)):
            fp = os.path.join(self.path, name)
            if os.path.islink(fp):
                print "WARNING, symbolic links not supported, anything might happen"
                print "symlink found:", fp
                if not self.symlink_warning:
                    # exit on symlink
                    import sys
                    sys.exit(1)
            elif os.path.isfile(fp):
                stat = os.stat(fp)
                if self.use_mtime:
                    self.contents.append('%s (%s@%s)' % (name, stat.st_size, stat.st_mtime))
                else:
                    self.contents.append('%s (%s)' % (name, stat.st_size))
                self.num_files += 1
                self.size += stat.st_size
            else:
                # directory
                dt = DirTree(fp, self.factory, self.use_mtime, self.symlink_warning)
                self.num_files += dt.num_files
                self.size += dt.size
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
        return 'size: %s\t files: %s \t%s' % (self.size, self.num_files, self.path)



class Factory(dict):
    """

    Factory stores all DirTrees by path for easy access,
    keeps order of keys.
    TODO-beb: replace with ordereddict from http://code.activestate.com/recipes/576693/
    """

    def __init__(self):
        self.ordered_keys = []

    def register(self, item):
        self.ordered_keys.append(item.path)
        self[item.path] = item

