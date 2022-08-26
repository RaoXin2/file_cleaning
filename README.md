# File Cleaning

the script is used for cleaning target files in an archive file, or a nested archive file (archive files inside archive file)
it's useful for oss cleaning

###inputs:
<li>a csv file:

| Package      | Description | Type        | Target      |
| -----------  | ----------- | ----------- | ----------- |
| pip 21.0.1   | t32         | exe         | pip 21.0.1/src/pip/_vendor/distlib/t32.exe |
| pip 21.0.1   | t64         | exe         | pip 21.0.1/src/pip/_vendor/distlib/t64.exe |
| ...   |...         | ...         | ... |

<li>a package (corresponding to the csv file):

pip 21.0.1.zip

###usage:
    python oss_clearing.py <path_to_your_package> <path_to_your_csv>

example:

    python oss_clearing.py ./manual_test/resources/pip 21.0.1.zip ./manual_test/resources/edge.csv

when done, an archive file with same name that ending with "-done" will be generated at same directory of your input package

###supported format:

<li>.zip
<li>.tar.gz
<li>.tar.xz

###unsupported format:
<li>.tar.lzma