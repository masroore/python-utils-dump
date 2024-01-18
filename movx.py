import pathlib,  sys, zipfile

if len(sys.argv) != 2:
    prefix = input("Prefix: ").strip()
else:
    prefix = sys.argv[1].strip()

base_folder = pathlib.Path('./')

zf = zipfile.ZipFile( base_folder / f'{prefix}.zip', "w" )
zf.compress_type= zipfile.ZIP_DEFLATED

for ix, folder_path in  enumerate(base_folder.glob('*/')):
    for file_path in folder_path.glob('*'):
        new_fpath = base_folder / f'{prefix}-{ix + 1}-{file_path.name}'
        file_path.rename(new_fpath)
        print(f'{file_path.name} >> {new_fpath.name}')

    zf.mkdir(folder_path.name)
    folder_path.rmdir()

zf.close()