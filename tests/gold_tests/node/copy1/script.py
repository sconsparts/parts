
import os

if not os.path.exists('foo'):
    os.makedirs("foo")
    open("foo/test1.txt",'w').write("hello")
    open("foo/test2.txt",'w').write("hello")
    open("foo/test3.txt",'w').write("hello")
    open("foo/test4.txt",'w').write("hello")


