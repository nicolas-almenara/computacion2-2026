def fibonacci(limite=None):
    a, b = 0, 1
    while limite is None or a <= limite:
        yield a
        a, b = b, a + b
fib = fibonacci()
for _ in range(10):
    print(next(fib))
print(next(fib))
print(next(fib))
for n in fibonacci(limite=100):
    print(n)