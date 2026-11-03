#1. Entrá a `http://localhost:8000/docs`. ¿Quién escribió esa documentación?
#Esa documentacion la genera automaticamente FastAPI.
#2. Probá los endpoints desde ahí. ¿Qué pasa si mandás un `tipo` que no está en la lista?
#Al mandar un tipo que no esta en la lista me tiro el error 422 'unprocessable entity', esto
#es porque estamos usando la funcion literal de la libreria typing.
#3. Mirá `http://localhost:8000/openapi.json`. ¿Qué es ese archivo?
#Es un archivo de tipo JSON el cual contiene informacion de toda la api, FastAPI lo genera
#automaticamente siguiendo el estandar openapi. A partir de este archivo FastAPI genera el
#/docs.
#4. Provocá cada uno de estos errores y anotá el código y el mensaje:
#"Input should be a valid integer, unable to parse string as an integer" 422 Unprocessable Entity.
#"Input should be 'descargar', 'hashear' or 'esperar'","input":"volar","ctx":{"expected":"'descargar', 'hashear' or 'esperar'"}}]} 422 Unprocessable Entity
#"Input should be less than or equal to 5","input":99,"ctx":{"le":5}}]} 422 Unprocessable Entity
#{"detail":"No existe esa tarea"} 404 Not Found
#5. ¿Cuáles dan 422 y cuál da 404? ¿Por qué son distintos?
#Los que dan 422 puede ser porque el tipo de dato es incorrecto, el valor
# no se encuentra en la lista de valores posibles de Literal o valor 
# fuera de rango, en cambio 404 es cuando el pedido es valido pero el recurso no existe.
#6. En el JSON de error hay un campo `loc`. ¿Qué información da?
#loc es una lista que indica donde esta el error, el primer elemento de la lista indica
#la parte del pedido (body, path, query o header) y el segundo en el nombre del campo en
#el que fallo.
#7. ¿En qué momento se ejecuta la validación: antes o después de tu función? Comprobalo con un `print`.
#Antes. Puse un print al inicio de crear(): con datos invalidos (tipo "volar" o prioridad 99)
#la API responde 422 y el print NO aparece; con datos validos responde 201 y el print si aparece.
#FastAPI valida el cuerpo con Pydantic segun las anotaciones antes de llamar a la funcion, asi que
#la funcion solo se ejecuta con datos ya validos.
#10. Hacé que `POST /tareas` rechace una tarea si ya hay 10 pendientes, con un código de estado apropiado. ¿Cuál elegís y por qué?
#Elijo el codigo de estado 503 service unavailable ya que el pedido es valido pero el servidor
#esta saturado y es una situacion temporal.
#11. Sacale la anotación `: int` al parámetro de `obtener()`. ¿Qué cambia al pedir `/tareas/abc`?
#Lo que cambiaria al quitar : int es que al hacer el pedido, este seria 'correcto' por lo que
#no lanzaria el codigo de error 422, sino que lanzaria 404 not found. Esto no ocurrira solo con
#/abc, tambien ocurriria por ejemplo con /1 ya que al quitar : int, deja de convertir el texto que
#llega a numero entero y sigue siendo un string.
#12. Cambiá `prioridad: int` por `prioridad: str` en el modelo. ¿Qué acepta ahora?
#Al realizar este cambio lo que se acepta ahora es string. Es decir cualquier tipo de 
#cadena de texto, pero perdemos los 'filtros' que aplicamos en string, por ejemplo 
#el rango de 1 a 5.
#13. ¿Qué tres cosas hace FastAPI con cada anotación de tipo?
#Convierte: transforma el dato que llego al tipo de dato indicado, valida: si el dato
#no se puede convertir, lanza 422 unprocessable entity. Documenta: genera documentacion
#automaticamente en /docs y en openapi.json.