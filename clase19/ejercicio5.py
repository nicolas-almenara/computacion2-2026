#1. Copiá los tres tiempos que te dio.
#  /async-bien    1.03s
#  /async-mal     3.01s
#  /sync          1.04s
#2. ¿Por qué `/async-mal` tarda el triple? Relacionalo con la regla de la clase 18.
#async-mal tarda el triple porque, porque time.sleep bloquea el event loop y como 
#es uno solo bloquea todos los pedidos.
#3. ¿Por qué `/sync` anda igual de bien que `/async-bien`, si también usa `time.sleep`?
#Esto pasa porque FastAPI detecta que /sync no es corrutina y lo manda a un threadpool por 
#lo tanto tambien se solapan.
#4. Entonces, ¿cuándo conviene `async def` y cuándo `def`? Escribí la regla.
#async def conviene cuando cuando se utiliza con await y bibliotecas asincronas, que permiten
#que el endpoint devuelva el control al event loop mientras espera y se puedan atender otros
#pedidos. Conviene usar un def comun cuando el codigo es bloqueante y FastAPI automaticamente
#lo ejecuta en un threadpool.
#5. Este endpoint, ¿está bien o mal escrito? Justificá.
#Este endpoint esta mal escrito ya que utliza la libreria request, la cual es bloqueante
#combinandolo con async, esto significa que se quedaria esperando sin ceder el control
#a otro endpoint, bloqueando es event loop.
#6. Arreglalo de dos formas distintas: una cambiando el `async def`, otra cambiando la biblioteca.
@app.get('/datos')
def datos():
    import requests
    return requests.get('https://api.ejemplo.com/cosas').json()

import httpx
@app.get('/datos')
async def datos():
    async with httpx.AsyncClient() as cliente:
        respuesta = await cliente.get('https://api.ejemplo.com/cosas')
        return respuesta 

#7. Agregale a `medir.py` un cuarto endpoint que haga cálculo pesado (un hash iterado). ¿Cuál de las tres formas conviene para eso? ¿Alguna lo resuelve bien?
#Conviene def comun porque no congela el event loop, pero de todas maneras ninguna forma
#lo resuelve bien, el GIL de python no permite que los threads ejecuten codigo de python 
#en paralelo. Lo que lo resuelve es usar procesos porque cada proceso tiene su propio GIL.