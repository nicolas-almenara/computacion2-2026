#!/usr/bin/env python3
"""Descargas reales con httpx: secuencial contra concurrente.

Uso (con el venv activado, que es donde está httpx):
    source venv/bin/activate
    python3 descargas_http.py
"""
import asyncio
import time

import httpx

URLS = ['https://example.com', 'https://nicolasalmenara.com']



async def bajar(cliente, url):
    r = await cliente.get(url)
    return url, r.status_code, len(r.content)


async def secuencial(cliente):
    return [await bajar(cliente, u) for u in URLS]


async def concurrente(cliente):
    return await asyncio.gather(*(bajar(cliente, u) for u in URLS), return_exceptions=True)

async def semaforo(cliente):
    s = asyncio.Semaphore(3)

    async def acotada(u):
        async with s:                       # cada descarga pide su permiso
            return await bajar(cliente, u)

    return await asyncio.gather(*(acotada(u) for u in URLS))

async def main():
    # Un solo AsyncClient para todas las descargas: reutiliza conexiones (keep-alive)
    async with httpx.AsyncClient(timeout=10) as cliente:
        for etiqueta, funcion in (('secuencial', secuencial),
                                  ('concurrente', concurrente),
                                  ('semaforo', semaforo)):
            t0 = time.perf_counter()
            try:
                resultados = await funcion(cliente)
            except Exception as e:
                # sin return_exceptions, una URL mala corta toda la funcion
                print(f'{etiqueta:<12} FALLO: {type(e).__name__}: {e}')
                continue
            dt = time.perf_counter() - t0
            print(f'{etiqueta:<12} {len(resultados)} resultados en {dt:5.2f}s')
            for r in resultados:
                if isinstance(r, Exception):
                    print(f'    ERROR: {type(r).__name__}: {r}')
                else:
                    print(f'    {r[1]}  {r[2]} bytes  {r[0]}')


if __name__ == '__main__':
    asyncio.run(main())
