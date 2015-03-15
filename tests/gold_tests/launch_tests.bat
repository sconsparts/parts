@pushd %~dp0
@pushd ..\..
@set PYTHONPATH=%CD%;%PYTHONPATH%
@popd
@python ..\gtest\gtest.py %*
@popd
@exit /B %ERRORLEVEL%
