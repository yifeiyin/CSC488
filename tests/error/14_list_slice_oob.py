# [RUNTIME] List slice out of bound. This behavior is different python
# RUNTIME ERROR: End index out of bounds. Trying to access 10, length is 4
a: [int] = [1,2,3,4]
b: [int] = a[0:10]
