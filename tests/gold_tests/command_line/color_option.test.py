Test.Summary='''
This test the --color cli option with no overrides.
Will test a number of good inputs and bad inputs
'''
Setup.Copy.FromTemplate('empty')

# note the --tc=null means we can set the target without issue of the tools complain 
# that the can't setup correctly
t=Test.AddTestRun("good")
t.Command="scons all --color --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --use-color --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --use-color=True --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --use-color=1 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --use-color=yes --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --use-color=default --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --use-color=darkbg --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --use-color=full --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good1.gold'

t=Test.AddTestRun("good")
t.Command="scons all --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good2.gold'

t=Test.AddTestRun("good")
t.Command="scons all --use-color=simple --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good3.gold'

# stdout 
t=Test.AddTestRun("stdout")
t.Command="scons all --use-color=stdout=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdout.gold'

t=Test.AddTestRun("stdout")
t.Command="scons all --use-color=o=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdout.gold'

t=Test.AddTestRun("stdout")
t.Command="scons all --use-color=out=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdout.gold'

 # console
t=Test.AddTestRun("console")
t.Command="scons all --use-color=con=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_console.gold'

t=Test.AddTestRun("console")
t.Command="scons all --use-color=tty=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_console.gold'

t=Test.AddTestRun("console")
t.Command="scons all --use-color=console=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_console.gold'

#stderr
t=Test.AddTestRun("stderr")
t.Command="scons all --use-color=stderr=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stderr.gold'

t=Test.AddTestRun("stderr")
t.Command="scons all --use-color=error=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stderr.gold'

t=Test.AddTestRun("stderr")
t.Command="scons all --use-color=err=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stderr.gold'

t=Test.AddTestRun("stderr")
t.Command="scons all --use-color=e=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stderr.gold'

#stdwrn
t=Test.AddTestRun("stdwrn")
t.Command="scons all --use-color=stdwrn=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdwrn.gold'

t=Test.AddTestRun("stdwrn")
t.Command="scons all --use-color=warning=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdwrn.gold'

t=Test.AddTestRun("stdwrn")
t.Command="scons all --use-color=wrn=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdwrn.gold'

t=Test.AddTestRun("stdwrn")
t.Command="scons all --use-color=w=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdwrn.gold'

#stdmsg
t=Test.AddTestRun("stdmsg")
t.Command="scons all --use-color=stdmsg=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdmsg.gold'

t=Test.AddTestRun("stdmsg")
t.Command="scons all --use-color=message=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdmsg.gold'

t=Test.AddTestRun("stdmsg")
t.Command="scons all --use-color=msg=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdmsg.gold'

t=Test.AddTestRun("stdmsg")
t.Command="scons all --use-color=m=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdmsg.gold'

#stdverbose
t=Test.AddTestRun("stdverbose")
t.Command="scons all --use-color=stdverbose=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdverbose.gold'

t=Test.AddTestRun("stdverbose")
t.Command="scons all --use-color=verbose=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdverbose.gold'

t=Test.AddTestRun("stdverbose")
t.Command="scons all --use-color=ver=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdverbose.gold'

t=Test.AddTestRun("stdverbose")
t.Command="scons all --use-color=v=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdverbose.gold'

#Debug
t=Test.AddTestRun("stdtrace")
t.Command="scons all --use-color=trace=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdtrace.gold'

t=Test.AddTestRun("stdtrace")
t.Command="scons all --use-color=trace=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdtrace.gold'

t=Test.AddTestRun("stdtrace")
t.Command="scons all --use-color=t=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_stdtrace.gold'

#color tests
#black
t=Test.AddTestRun("black")
t.Command="scons all --use-color=t=0 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_black.gold'

t=Test.AddTestRun("black")
t.Command="scons all --use-color=t=black --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_black.gold'

t=Test.AddTestRun("black")
t.Command="scons all --use-color=t=blk --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_black.gold'

#red
t=Test.AddTestRun("red")
t.Command="scons all --use-color=t=1 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_red.gold'

t=Test.AddTestRun("red")
t.Command="scons all --use-color=t=red --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_red.gold'

t=Test.AddTestRun("red")
t.Command="scons all --use-color=t=r --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_red.gold'

#green
t=Test.AddTestRun("green")
t.Command="scons all --use-color=t=2 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_green.gold'

t=Test.AddTestRun("green")
t.Command="scons all --use-color=t=green --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_green.gold'

t=Test.AddTestRun("green")
t.Command="scons all --use-color=t=g --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_green.gold'

#yellow
t=Test.AddTestRun("yellow")
t.Command="scons all --use-color=t=3 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_yellow.gold'

t=Test.AddTestRun("yellow")
t.Command="scons all --use-color=t=yellow --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_yellow.gold'

t=Test.AddTestRun("yellow")
t.Command="scons all --use-color=t=y --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_yellow.gold'

#blue
t=Test.AddTestRun("blue")
t.Command="scons all --use-color=t=4 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_blue.gold'

t=Test.AddTestRun("blue")
t.Command="scons all --use-color=t=blue --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_blue.gold'

t=Test.AddTestRun("blue")
t.Command="scons all --use-color=t=b --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_blue.gold'

#purple
t=Test.AddTestRun("purple")
t.Command="scons all --use-color=t=5 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_purple.gold'

t=Test.AddTestRun("purple")
t.Command="scons all --use-color=t=purple --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_purple.gold'

t=Test.AddTestRun("purple")
t.Command="scons all --use-color=t=magenta --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_purple.gold'

t=Test.AddTestRun("purple")
t.Command="scons all --use-color=t=p --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_purple.gold'

t=Test.AddTestRun("purple")
t.Command="scons all --use-color=t=m --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_purple.gold'

#aqua
t=Test.AddTestRun("aqua")
t.Command="scons all --use-color=t=6 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_aqua.gold'

t=Test.AddTestRun("aqua")
t.Command="scons all --use-color=t=aqua --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_aqua.gold'

t=Test.AddTestRun("aqua")
t.Command="scons all --use-color=t=cyan --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_aqua.gold'

t=Test.AddTestRun("aqua")
t.Command="scons all --use-color=t=a --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_aqua.gold'

t=Test.AddTestRun("aqua")
t.Command="scons all --use-color=t=c --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_aqua.gold'

#white
t=Test.AddTestRun("white")
t.Command="scons all --use-color=t=7 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_white.gold'

t=Test.AddTestRun("white")
t.Command="scons all --use-color=t=white --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_white.gold'

t=Test.AddTestRun("white")
t.Command="scons all --use-color=t=lightgray --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_white.gold'

t=Test.AddTestRun("white")
t.Command="scons all --use-color=t=lightgrey --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_white.gold'

t=Test.AddTestRun("white")
t.Command="scons all --use-color=t=w --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_white.gold'

t=Test.AddTestRun("white")
t.Command="scons all --use-color=t=lg --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_white.gold'

#gray
t=Test.AddTestRun("gray")
t.Command="scons all --use-color=t=8 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_gray.gold'

t=Test.AddTestRun("gray")
t.Command="scons all --use-color=t=gray --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_gray.gold'

t=Test.AddTestRun("gray")
t.Command="scons all --use-color=t=grey --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_gray.gold'

#bright red
t=Test.AddTestRun("brightred")
t.Command="scons all --use-color=t=9 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightred.gold'

t=Test.AddTestRun("brightred")
t.Command="scons all --use-color=t=brightred --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightred.gold'

t=Test.AddTestRun("brightred")
t.Command="scons all --use-color=t=br --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightred.gold'

#bright green
t=Test.AddTestRun("brightgreen")
t.Command="scons all --use-color=t=10 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightgreen.gold'

t=Test.AddTestRun("brightgreen")
t.Command="scons all --use-color=t=brightgreen --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightgreen.gold'

t=Test.AddTestRun("brightgreen")
t.Command="scons all --use-color=t=bg --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightgreen.gold'

#bright yellow
t=Test.AddTestRun("brightyellow")
t.Command="scons all --use-color=t=11 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightyellow.gold'

t=Test.AddTestRun("brightyellow")
t.Command="scons all --use-color=t=brightyellow --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightyellow.gold'

t=Test.AddTestRun("brightyellow")
t.Command="scons all --use-color=t=by --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightyellow.gold'

#bright blue
t=Test.AddTestRun("brightblue")
t.Command="scons all --use-color=t=12 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightblue.gold'

t=Test.AddTestRun("blue")
t.Command="scons all --use-color=t=brightblue --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightblue.gold'

t=Test.AddTestRun("blue")
t.Command="scons all --use-color=t=bb --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightblue.gold'

#bright purple
t=Test.AddTestRun("brightpurple")
t.Command="scons all --use-color=t=13 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightpurple.gold'

t=Test.AddTestRun("brightpurple")
t.Command="scons all --use-color=t=brightpurple --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightpurple.gold'

t=Test.AddTestRun("brightpurple")
t.Command="scons all --use-color=t=brightmagenta --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightpurple.gold'

t=Test.AddTestRun("brightpurple")
t.Command="scons all --use-color=t=bm --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightpurple.gold'

t=Test.AddTestRun("brightpurple")
t.Command="scons all --use-color=t=bp --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightpurple.gold'

#bright aqua
t=Test.AddTestRun("brightaqua")
t.Command="scons all --use-color=t=14 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightaqua.gold'

t=Test.AddTestRun("brightaqua")
t.Command="scons all --use-color=t=brightaqua --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightaqua.gold'

t=Test.AddTestRun("brightaqua")
t.Command="scons all --use-color=t=brightcyan --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightaqua.gold'

t=Test.AddTestRun("brightaqua")
t.Command="scons all --use-color=t=ba --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightaqua.gold'

t=Test.AddTestRun("brightaqua")
t.Command="scons all --use-color=t=bc --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightaqua.gold'

#bright white
t=Test.AddTestRun("brightwhite")
t.Command="scons all --use-color=t=15 --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightwhite.gold'

t=Test.AddTestRun("brightwhite")
t.Command="scons all --use-color=t=brightwhite --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightwhite.gold'

t=Test.AddTestRun("brightwhite")
t.Command="scons all --use-color=t=bw --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_brightwhite.gold'

#default
t=Test.AddTestRun("default")
t.Command="scons all --use-color=t=default --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_default.gold'

#bright
t=Test.AddTestRun("bight")
t.Command="scons all --use-color=t=bright --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_bold.gold'

t=Test.AddTestRun("bight")
t.Command="scons all --use-color=t=bold --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_bold.gold'

#dim
t=Test.AddTestRun("dim")
t.Command="scons all --use-color=t=dim --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_dim.gold'

#mass set
t=Test.AddTestRun("good")
t.Command="scons all --use-color=c=r:g,o=y:b,e=g:br,w=3:4,m=10:13,v=bold:default,t=blk:white --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode=0
t.Streams.Debug='gold/color_good4.gold'

t = Test.AddTestRun("bad")
t.Command = "scons all --use-color=foo --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode = 2
t.Streams.stderr = ['gold/color_bad1.scons23.gold', 'gold/color_bad1.scons21.gold']

t = Test.AddTestRun("bad")
t.Command = "scons all --use-color=c=r:g,o=y,b:e=g:br,w=3:4,m=10:13,v=bold:default,t=blk:white --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode = 2
t.Streams.stderr = ['gold/color_bad2.scons23.gold', 'gold/color_bad2.scons21.gold']

t = Test.AddTestRun("bad")
t.Command = "scons all --use-color=stdout=badcolor --trace=use_color_option --tc=null --console-stream=none"
t.ReturnCode = 2
t.Streams.stderr = ['gold/color_bad3.scons23.gold', 'gold/color_bad3.scons21.gold']
