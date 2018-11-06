Test.Summary = '''
Problem:
Building the sample with Parts 0.10.5 results in pickling errors.

Stack trace:
PicklingError: Can't pickle <class 'SCons.Util.UniqueList'>: it's not the same object as SCons.Util.UniqueList:
  File "C:\Python26\scons-2.1.0\SCons\Script\Main.py", line 1342:
    _exec_main(parser, values)
  File "C:\Python26\scons-2.1.0\SCons\Script\Main.py", line 1306:
    _main(parser)
  File "C:\Python26\scons-2.1.0\SCons\Script\Main.py", line 1070:
    nodes = _build_targets(fs, options, targets, target_top)
  File "C:\Python26\lib\site-packages\parts\overrides\build_hook.py", line 14:
    if glb.engine.Process(fs, options, targets, target_top) == False:
  File "C:\Python26\lib\site-packages\parts\engine.py", line 266:
    self.PostProcessEvent(self.__build_mode)
  File "C:\Python26\lib\site-packages\parts\events\__init__.py", line 33:
    callback(*args, **kargs)
  File "C:\Python26\lib\site-packages\parts\pnode\pnode_manager.py", line 317:
    self.StorePNode(node)
  File "C:\Python26\lib\site-packages\parts\pnode\pnode_manager.py", line 309:
    self.store_value(pnode,sd,valuestostore)
  File "C:\Python26\lib\site-packages\parts\pnode\pnode_manager.py", line 244:
    'pinfo':pickle.dumps(_info)
'''
Setup.Copy.FromDirectory('source')

Test.AddBuildRun('all').ReturnCode = 0
