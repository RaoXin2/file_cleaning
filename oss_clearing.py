import shutil
import os
import sys

SUPPORT_FORMAT = ['.zip', '.tar.gz', '.tar.xz']
UNSUPPORTED_FORMAT = ['.tar.lzma']

class Archive:
    def __init__(self, archive_path: str):
        self._target_files = []
        self._target_archives = []
        self._pkg_path = archive_path
        self._cwd, self._type = self.__get_cwd(archive_path)

    def remove_files(self):
        pass

    def __get_cwd(self, path):
        for item in SUPPORT_FORMAT:
            if path[-len(item):] == item:
                # print(path[:-len(item)], item)
                return path[:-len(item)], item

        # TODO: Not found, unsupported format

    @property
    def pkg_path(self):
        return self._pkg_path

    @pkg_path.setter
    def pkg_path(self, path):
        self._pkg_path = path

    def _pack(self, base_dir):
        pth = os.path.join(base_dir, self._cwd)
        if self._type == SUPPORT_FORMAT[0]:
            shutil.make_archive(base_name=pth,
                                format='zip',
                                root_dir=pth)
        if self._type == SUPPORT_FORMAT[1]:
            shutil.make_archive(base_name=pth,
                                format='gztar',
                                root_dir=pth)
        if self._type == SUPPORT_FORMAT[2]:
            shutil.make_archive(base_name=pth,
                                format='xztar',
                                root_dir=pth)

    def process(self, base_dir):
        shutil.unpack_archive(os.path.join(base_dir, self._pkg_path),
                              os.path.join(base_dir, self._cwd)) # os.path.dirname(self._cwd)
        os.remove(os.path.join(base_dir, self._pkg_path))
        # remove marked files
        for file in self._target_files:
            os.remove(os.path.join(base_dir, file))
        for arc in self._target_archives:
            arc.process(base_dir)
        self._pack(base_dir)

    def process_line(self, str):
        if self._check_supported_format(SUPPORT_FORMAT, str) is None:
            self._target_files.append(str)
        else:
            next_pack, remains = self._split_line(str)
            if next_pack is None:
                return
            # print("next pkg: ", next_pack)
            # print("remains: ", remains)
            arc_found = False
            for arc in self._target_archives:
                if arc._pkg_path == next_pack:
                    arc.process_line(remains)
                    arc_found = True
            if not arc_found:
                new_arc = Archive(next_pack)
                self._target_archives.append(new_arc)
                new_arc.process_line(remains)

    def _split_line(self, line):
        splt = line.split('/')
        for t in splt:
            file_ext = self._check_supported_format(SUPPORT_FORMAT, t)
            if file_ext is not None:
                temp = line.split(t)
                if temp[1] == '':
                    self._target_files.append(line)
                    return None, None
                next_pkg = temp[0] + t
                remains = line.replace(next_pkg, '')
                return next_pkg, next_pkg.replace(file_ext, '') + remains

    def _check_supported_format(self, list, str):
        for item in list:
            if item in str:
                return item
        return None


def process_csv(csv_path, root_archive):
    with open(csv_path) as file:
        all_lines = file.readlines()
    file.close()
    line_count = 0
    for line in all_lines:
        spt = True
        if line_count == 0:
            line_count += 1
            continue
        pth = line.split(',')[3].strip()
        for item in UNSUPPORTED_FORMAT:
            if item in pth:
                print(f'Path: {pth} contains unsupported archive type')
                spt = False
                break
        if not spt:
            continue
        root_archive.process_line(pth)
        line_count += 1


if __name__ == '__main__':
    input_archive = 'D:/github/file_cleaning/manual_test/resources/pip-21.0.1.zip'
    input_csv = 'D:/github/file_cleaning/manual_test/resources/edge.csv'
    # base_dir = os.path.dirname(input_archive)
    base_dir = input_archive.replace('.zip', '')
    arc_name = os.path.basename(input_archive)
    a = Archive("../" + arc_name)
    a._cwd = ''
    process_csv('D:/github/file_cleaning/manual_test/resources/edge.csv', a)
    a.process(base_dir)
