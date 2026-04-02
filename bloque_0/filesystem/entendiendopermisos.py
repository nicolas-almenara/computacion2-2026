#Error al ejecutar:
#Permission denied
#¿Por qué?
#Porque el archivo no tiene permiso de ejecución.
#Significado de -rw-r--r--:
#El primero es el tipo (archivo normal).
#Después:
#rw- → el dueño puede leer y escribir
#r-- → el grupo solo puede leer
#r-- → los demás solo pueden leer
#Diferencia entre chmod +x y chmod 755:
#chmod +x solo agrega permiso de ejecución.
#chmod 755 fija todo: dueño puede leer, escribir y ejecutar; grupo y otros pueden leer y ejecutar.
#Permisos 644:
#Todos pueden leer, pero solo el dueño puede escribir.
#¿Por qué los directorios necesitan x?
#Porque sin ese permiso no podés entrar al directorio, aunque puedas verlo.