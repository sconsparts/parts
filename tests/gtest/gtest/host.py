import glb

def WriteMessage(*lst,**kw):
    glb.Engine.Host.WriteMessage(kw.get('sep',' ').join(lst)+kw.get('end','\n'))

def WriteWarning(*lst,**kw):
    glb.Engine.Host.WriteWarning(kw.get('sep',' ').join(lst)+kw.get('end','\n'),
                                 kw.get('stackframe',None),
                                 kw.get('show_stack',True))

def WriteError(*lst,**kw):
    glb.Engine.Host.WriteError(kw.get('sep',' ').join(lst)+kw.get('end','\n'),
                               kw.get('stackframe',None),
                               kw.get('show_stack',True))

def WriteDebug(catagory,*lst,**kw):
    if glb.Engine:
        if catagory.lower() in glb.Engine.Host.DebugCatagories or \
        'all' in glb.Engine.Host.DebugCatagories:
            glb.Engine.Host.WriteDebug(catagory,kw.get('sep',' ').join(lst)+kw.get('end','\n'))

def WriteVerbose(catagory, *lst, **kw):
    if glb.Engine:
        if catagory.lower() in glb.Engine.Host.VerboseCatagories or \
        'all' in glb.Engine.Host.VerboseCatagories:
            glb.Engine.Host.WriteVerbose(catagory,kw.get('sep',' ').join(lst)+kw.get('end','\n'))

def WriteProgress(task,msg=None,progress=None,completed=False):
    glb.Engine.Host.WriteProgress(task,msg,progress,completed)
