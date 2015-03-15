@echo off

REM  This batch file displays the current version of the Parts extension module.
REM  Remove REM from the following two lines if you want the version to be shown only 
REM  when '-v' is specified.
REM
REM if '%1' == '-v' goto ShowVersion
REM goto Exit
REM

:ShowVersion
python -c "from os.path import join; import sys; sys.path = [ join(sys.prefix, 'lib', 'site-packages', 'parts')] + sys.path; import parts_version; print 'Parts Version:', parts_version._PARTS_VERSION"

:Exit
