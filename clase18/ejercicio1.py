def tarea():
    yield 'trabajando'
    return 'resultado final'

t = tarea()
next(t)
try:
    next(t)
except StopIteration as e:
    print(e.value)

#1. ¿Qué pasa si hacés `a.send(10)` sin llamar antes a `next(a)`? Probalo y leé el error.
#El error es 'TypeError: can't send non-None value to a just-started generator'. Ocurre porque
#a un generador recien arrancado que todavia no llega a su primer yield, solo se le puede enviar
#none al principio, que es justamente lo que hacer next(a) (a.send(None)).

#2. Después del `next(a)` inicial, ¿qué devuelve? ¿Por qué ese valor?
#Despues del next(a) inicial devuelve 0, esto es porque ejecuta el generador desde
#el principio hasta el primer yield, ahi se pausa y emite el valor que tiene total en
#ese momento.

#3. Hacé tres `send()` seguidos y explicá de dónde sale cada resultado.
#El primer resultado sale de que envia n=10, se suma a total y total=10
#el segundo resultado sale de que n=15, se suma al total(10) y total=25,
#el tercer resultado sale de que n=20, se suma a total(25) y total =45.

#4. Creá dos generadores de `contador()` y alterná `next()` entre ellos. ¿Comparten el `n`?
#No no lo comparten, cada uno lleva su propia cuenta de n.

#5. ¿Dónde vive ese `n` mientras el generador está suspendido? Compará con una variable local de una función común.
#Ese n vive en su frame mientras el generador esta suspendido, en una funcion comun una variable local se pierde al
#terminar (return).

#6. ¿Qué imprime? ¿Por qué el `return` de un generador no se obtiene como en una función normal?
#Imprime resultado final, el return de un generador no se obtiene como en una funcion normal
#porque ya se esta devolviendo valores con yield, en cambio cuando llega return, python lo usa
#como señal de fin y lanza StopIteration guardando ese valor en e.value.

#7. ¿Cómo usó nuestro scheduler esta excepción?
#Nuestro scheduler utilizo esta excepcion para marcar el final del generador.

