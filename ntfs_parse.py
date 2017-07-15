import sys
import logging
import argparse

import fs_ntfs
import DataModel


def arg_options():

    usage = """Usage: example.py \\\\.\\c: -f 0 --fetch-file
       example.py \\\\.\\c: -s $MFT --fetch-file
       example.py \\\\.\\c: -s $MFTMirr
       example.py \\\\.\\c: -s C:\pagefile.sys --fetch-file
       example.py \\\\.\\c: -s "Documents and Settings\\All Users\\Application Data\\Start Menu\\desktop.ini" --fetch-file
           note: ?:\ and quotes will be skipped.
       example.py ntfs_image -f 123 --fetch-file
       """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=usage)
    parser.add_argument("image", help="NTFS files-system image.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--filerecord", help="Dump info for file record number.", type=int)
    group.add_argument("-s", "--search", help="Search path. Will dump all info traversing directories.")

    parser.add_argument("-w", "--fetch-file", help="Fetch all file's streams.", action="store_true")
    parser.add_argument("-l", "--list", help="List files, specify recursion depth (default is 2). Give -1 for a full recursion.", type=int, nargs='?', const=2)

    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument("-q", "--quiet", help="No logging.", action="store_true")
    group1.add_argument("-L", "--log-file", help="Write to this logfile.")


    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    return args

def save_it(fr):
    if fr is None:
        print('file was not found, nothing to fetch.')
        return

    filename = fr.get_displayed_filename()

    streams = fr.get_file_streams()
    
    for s in streams:
        save_filename = filename
        display_filename = filename
        if s:
            save_filename = filename + '_' + s
            display_filename = filename + ':' + s
       
        fo = open(save_filename, 'wb+')
        print('fetching file "{}", size {:,} bytes...'.format(display_filename, fr.get_file_size(stream=s)))

        fr.fetch_file(fo, stream=s)
        fo.close()

def print_dir(dirs, delim='  '):

    import textwrap

    for root in dirs:
        #print(''.format(root))
        text = textwrap.indent(root, delim + '|- ')
        print(text)
        if dirs[root] is not None:
            print_dir(dirs[root], delim + '   ')
    

def main():
    args = arg_options()

    logger = logging.getLogger()

    if args.quiet:
        logger.addHandler(logging.NullHandler())
    else:
        logfile = '!logfile-ntfsparser'
        if args.log_file:
            logfile = args.log_file
        logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)



    logger = logging.getLogger(__name__)

    image = args.image.strip('"')
    
    mymft = fs_ntfs.MFT(DataModel.FileDataModel(image))

    mymft._get_mft_data_runs()
    mymft._build_attrdef()

    if args.filerecord is not None:
        fr = mymft.get_file_record(args.filerecord)

    if args.search is not None:
        name = args.search
        name = name.strip('"')
        if len(name) > 3:
            if name[1] == ':' and name[2] == '\\':
                name = name[3:]

        fr = mymft.get_filerecord_of_path(args.search)
        if fr is None:
            print('file was not found.')

    if args.list:
        dirs = fr.list_dir(args.list)
        name = fr.get_displayed_filename()

        dirs = {name: dirs}
        print_dir(dirs)

    if args.fetch_file:
        save_it(fr)

    print('\ndone, see log file.')
    return

if __name__ == '__main__':
    main()
