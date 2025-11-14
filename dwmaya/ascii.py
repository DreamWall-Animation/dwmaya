__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import codecs


ENCODING = 'iso-8859-1'


def iterate_over_maya_ascii_lines(maya_file_path):
    with codecs.open(maya_file_path, 'r', encoding=ENCODING) as mayascii:
        current_line = ''
        for line in mayascii:
            # Skip comments and metadata
            if line.startswith('//'):
                continue
            if line.startswith('applyMetadata'):
                continue
            line = line.strip()
            # handle file lines not ending with ";" as single maya lines:
            if not line.endswith(';'):
                current_line += line
                continue
            else:
                parts = line.split(';')
                # yield first part:
                yield current_line + parts[0] + ';'
                # yield whatever is between first and last part:
                for part in parts[1:-1]:
                    yield part + ';'
                # add last part is begining of next line (almost always empty):
                current_line = parts[-1]


def get_line_path(line):
    if line.startswith(('//', 'applyMetadata')):
        return
    try:
        path = line.split('"')[-2]
    except IndexError:
        return
    if not path.count('/') > 3 and not path.count('\\') > 3:
        return
    if '\\n' in path:
        return
    if path.endswith('.ma') and not line.startswith('file -r '):
        return
    return path
