import os
import sys
import stat
import pwd
import grp
from datetime import datetime
ruta = sys.argv[1]
info = os.lstat(ruta)
if stat.S_ISREG(info.st_mode):
    tipo = "archivo regular"
elif stat.S_ISDIR(info.st_mode):
    tipo = "directorio"
elif stat.S_ISLNK(info.st_mode):
    tipo = "enlace simbólico"
elif stat.S_ISCHR(info.st_mode):
    tipo = "dispositivo de caracteres"
else:
    tipo = "otro"
permisos = stat.filemode(info.st_mode)
usuario = pwd.getpwuid(info.st_uid).pw_name
grupo = grp.getgrgid(info.st_gid).gr_name
tam = info.st_size
inode = info.st_ino
links = info.st_nlink
creacion = datetime.fromtimestamp(info.st_ctime)
modificacion = datetime.fromtimestamp(info.st_mtime)
acceso = datetime.fromtimestamp(info.st_atime)
print(f"Archivo: {ruta}")
print(f"Tipo: {tipo}")
print(f"Tamaño: {tam} bytes")
print(f"Permisos: {permisos}")
print(f"Propietario: {usuario} (uid: {info.st_uid})")
print(f"Grupo: {grupo} (gid: {info.st_gid})")
print(f"Inodo: {inode}")
print(f"Enlaces duros: {links}")
print(f"Creación: {creacion}")
print(f"Última modificación: {modificacion}")
print(f"Último acceso: {acceso}")
if stat.S_ISLNK(info.st_mode):
    destino = os.readlink(ruta)
    print(f"Apunta a: {destino}")
if stat.S_ISDIR(info.st_mode):
    cantidad = len(os.listdir(ruta))
    print(f"Contenido: {cantidad} elementos")