import sys
import os
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage {0} outfile infile [infile1 infileN]".format(sys.argv[0])
        sys.exit(1)

    for i in sys.argv[2:]:
        if not os.path.exists(i):
            print "{0} was not found".format(i)
            sys.exit(1)
    ofile = file(sys.argv[1], "w")
    for i in sys.argv[2:]:
        f = file(i, "r")
        ofile.write("Data:{0}[\n".format(i))
        ofile.write(f.read())
        ofile.write("]:EndData:{0}\n".format(i))
