import shutil
import os
import sys
import tarfile
import zipfile

import numpy as np

SUPPORT_FORMAT = ['.zip', '.tar.gz', '.tar.xz', '.tar', '.npz', '.whl']
UNSUPPORTED_FORMAT = ['.tar.lzma']


class Archive:
    def __init__(self, archive_path: str):
        self._target_files = []
        self._target_archives = []
        self._pkg_path = archive_path
        self._cwd, self._type = self.__get_cwd(archive_path)
        self._is_root_node = False

    def remove_files(self, base, file_path):
        target_path = os.path.join(base, file_path)
        try:
            os.remove(target_path)
            # print(f'successfully remove file: {target_path}')
        except Exception:
            print(f"Cannot found file: {target_path}")

    def __get_cwd(self, path):
        """ generate current working directory for each archive node """
        for item in SUPPORT_FORMAT:
            if path[-len(item):] == item:
                # print(path[:-len(item)], item)
                return path[:-len(item)], item

    @property
    def pkg_path(self):
        """ get package path """
        return self._pkg_path

    @pkg_path.setter
    def pkg_path(self, path):
        """ set package path """
        self._pkg_path = path

    def _pack(self, bd):
        """ helper method to pack the archive"""
        pth = os.path.join(bd, self._cwd)
        base_path = pth
        if self._is_root_node:
            base_path = base_path[:-1] + '-done'
        if self._type == SUPPORT_FORMAT[0]:
            shutil.make_archive(base_name=base_path,
                                format='zip',
                                root_dir=pth)
        if self._type == SUPPORT_FORMAT[1]:
            shutil.make_archive(base_name=base_path,
                                format='gztar',
                                root_dir=pth)
        if self._type == SUPPORT_FORMAT[2]:
            shutil.make_archive(base_name=base_path,
                                format='xztar',
                                root_dir=pth)
        if self._type == SUPPORT_FORMAT[3]:
            shutil.make_archive(base_name=base_path,
                                format='tar',
                                root_dir=pth)
        if self._type == SUPPORT_FORMAT[5]:
            shutil.make_archive(base_name=base_path,
                                format='zip',
                                root_dir=pth)
            os.rename(pth + '.zip', pth + '.whl')
        # remove the uncompressed folder
        shutil.rmtree(pth)

    def _unpack(self, bd):
        try:
            if self._pkg_path.split('.')[-1] == 'tar':
                with tarfile.open(os.path.join(bd, self._pkg_path)) as tar:
                    tar.extractall(os.path.join(bd, self._cwd))
            elif self._type == '.whl':
                # print(os.path.join(bd, self._pkg_path))
                # print(os.path.join(bd, self._pkg_path)[:-4] + '.zip')
                os.rename(os.path.join(bd, self._pkg_path), os.path.join(bd, self._pkg_path)[:-4] + '.zip')
            else:
                shutil.unpack_archive(os.path.join(bd, self._pkg_path),
                                      os.path.join(bd, self._cwd))  # os.path.dirname(self._cwd)
        except Exception as e:
            print(f'uncompress issue[{e.winerror}]:{e.strerror}')

    def process(self, bd):
        """
        process the Archive tree, DFS - style
        for each Archive node, do following:
            - unpack the archive
            - delete target files in this archive
            - zip it back
        :param base_dir: base directory of the root node
        :return:
        """
        if self._type == '.npz':
            self.handle_npz(bd)
            return

        self._unpack(bd)
        if not self._is_root_node:
            if self._type != '.whl':
                os.remove(os.path.join(bd, self._pkg_path))
            else:
                shutil.unpack_archive(os.path.join(bd, self._pkg_path)[:-4] + '.zip',
                                      os.path.join(bd, self._cwd))
                os.remove(os.path.join(bd, self._pkg_path)[:-4] + '.zip')
        # remove marked files
        for file in self._target_files:
            self.remove_files(bd, file)
            # os.remove(os.path.join(base_dir, file))
        for arc in self._target_archives:
            arc.process(bd)
        self._pack(bd)

    def handle_npz(self, bd):
        temp = np.load(os.path.join(bd, self._pkg_path), allow_pickle=True, encoding="latin1")
        cmd = "np.savez(os.path.join(bd, self._pkg_path)"
        ls = []
        datas = []
        for f in self._target_files:
            ls.append(f.split('/')[-1].replace('.npy', ''))
        count = 0
        for data in temp.files:
            if data not in ls:
                # d[data] = temp[f'{data}']
                datas.append(temp[f'{data}'])
                cmd = cmd + f' ,{data}=datas[{count}] '
                count += 1
        cmd = cmd + ')'
        temp.close()
        os.remove(os.path.join(bd, self._pkg_path))
        exec(cmd)
        print()

        # np.savez(os.path.join(bd, self._pkg_path))
        # for file in temp.files:
        #     print(temp[f'{file}'])


    def process_line(self, str):
        """
        process one line from csv
        based on this line:
            - add file path to current node if no archive in the path
            - create a new Archive object if there is a new archive that no been added
            - add file to existing archive object if there is a archive and has been created
        :param str: a path string
        """
        # path with no zip file, mark the file directly
        if self._check_supported_format(SUPPORT_FORMAT, str) is None:
            self._target_files.append(str)
        else:
            next_pack, remains = self._split_line(str)
            if next_pack is None:
                return
            arc_found = False
            # try to find if next archive file is already exist in the archive tree
            for arc in self._target_archives:
                # if found, process the rest path
                if arc._pkg_path == next_pack:
                    arc.process_line(remains)
                    arc_found = True
            # if not found, create the new node, add it to the tree and process the rest line
            if not arc_found:
                new_arc = Archive(next_pack)
                self._target_archives.append(new_arc)
                new_arc.process_line(remains)

    def _split_line(self, line):
        """
        split the line to get the next archive path,
        and remaining path to files which inside this archive and must be deleted
        :param line: a line in csv
        :return: next archive path, remaining file path
        """
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
        """
        check if the format is supported
        :param list: list of supported archive format
        :param str: a line of file path
        :return: the type, or None if it is unsupported
        """
        for item in list:
            if item in str:
                return item
        return None


def process_csv(csv_path, root_archive):
    """
    process csv line by line, use the input to build up the archive structure tree
    :param csv_path: path to csv
    :param root_archive:
    """
    with open(csv_path) as file:
        all_lines = file.readlines()
    file.close()
    line_count = 0
    for line in all_lines:
        spt = True
        # skip the first line
        if line_count == 0:
            line_count += 1
            continue
        # get path from the 4th column
        pth = line.split(',')[3].strip()
        # check for unsupported type
        for item in UNSUPPORTED_FORMAT:
            if item in pth:
                print(f'Path: {pth} contains unsupported archive type')
                spt = False
                break
        if not spt:
            continue
        # process the line from root node
        root_archive.process_line(pth)
        line_count += 1


def initialize_root_archive(pkg):
    """
    initialize root node, the archive imported from user
    :param pkg: path to archive provided by user
    :return: root Archive object
    """
    arc_name = os.path.basename(pkg)
    a = Archive("../" + arc_name)
    a._cwd = ''
    a._is_root_node = True
    return a


if __name__ == '__main__':
    # check input parameters
    if len(sys.argv) < 3:
        print('Missing arguments! Usage: python oss_clearing.py')

    # assign input
    input_archive = sys.argv[1]
    input_csv = sys.argv[2]

    # handle base directory and root node
    base_dir = input_archive.replace('.zip', '')
    root = initialize_root_archive(input_archive)

    # process csv file by line
    process_csv(input_csv, root)

    # recursively process: unpack, delete, and pack up
    root.process(base_dir)
