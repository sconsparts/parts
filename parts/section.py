from SCons.Debug import logInstanceCreation


class section_delegator(object):
    ''' This class is the object the Parts object will deal with. It is created in a lazy manner by the meta form instance of
    the section_t class. This allow for reduce memory overhead for Parts that don't use the new format and also ensures that
    better scaling happen when we have cases of lots of Parts and lots of custom section are defined, as a Part is likely to use
    only a few of the possible full set that could be defined.
    '''


class section_t(object):
    ''' This class is the primary template used to create all section instances in Parts. It provides
    the basic wrapper code to handle the different cases the can be used in the declorator syntax.
    Internally it will create a instance object with data needed by the Part object to handle what the
    user defined for a given section. If no sections are defined, then the part_t object will not have any internal
    section object defined in it.
    '''

    def __init__(self, func=None, **kw):
        '''
        Defines the basic setup logic
         @param func defines the function we are wrapping. If None then lst or kw will have meta values we will want to process
         @param **kw a dictionary of name arguments to process

         add more doc info
        '''
        if __debug__:
            logInstanceCreation(self)
        # these values are added by the section object when it make the finial meta class
        # self._delegator_type this type we want to create
        # self._proxy Instance of the delegator type, else None
        # self._pobj instance of the Part object that we are defining ourselves on

        # data for this instance
        self._func = func
        self._kw = kw


def default_test_func(self, *lst, **kw):
    for l in lst:
        if callable(l):
            if l(self.env) == False:
                return False
        else:
            # error.. must be a callable type
            pass

    for k, v in kw.iteritems():
        try:
            if not (self.env[k] == v):
                return False
        except KeyError:
            return False
    return True


class section(object):
    ''' this class allows for the creation of a "Section" in the Parts file
    A section is a set of functions or phases that are used to setup state to
    do some set of actions. The main difference over the classic functional way
    is that this allow control over the processing of section or phases based on
    the target value and otehr logic tha section can define in how it processed
    the different phases.
    '''

    def __init__(self, name, processfunc, concepts_namspaces):
        '''
        name-- is the name of the section
        processfunc-- is a function(...) that will be called to process the
        section by the part manger object
        concept_namespaces-- is a list of namespaces that will be made to bind
        this section with a global target
        '''
        if __debug__:
            logInstanceCreation(self)
        self.dict = {
            '_phases': [],
            # 'Process':processfunc
        }
        self.name = name
        self.concepts = concepts_namspaces
        self.processfunc = processfunc

    def AddPhase(self, name, test_func=None, optional=False):
        '''
        This function will define a new phase for a given section
        name-- is the name of phase
        test_func-- is an optional function that will test attribute for seeing
        if this "case" shoudl be processed
        optional-- tells that this phase does not have to be defined to have a fully
        valid section
        '''

        def _phase(self, func, *lst, **kw):
            # allows us to make sure this function was only processed once after it has passed
            # this is faster than doing the full test if we know we can skip out
            if func.__dict__.get("parts_processed_passed", False) == True:
                return func
            if getattr(self, 'test_' + name)(*lst, **kw):
                getattr(self, 'func_' + name).append(func)
                func.parts_processed_passed = True
            return func

        def phase(self, func=None, *lst, **kw):
            if func is None:
                # return lamda function ( arg where passed in)
                return lambda x: getattr(self, '__' + name)(x, *lst, **kw)
            else:
                # return result of function call ( no args where passed in)
                return getattr(self, '__' + name)(func, *lst, **kw)

        if test_func is None:
            test_func = default_test_func

        # add phase data list
        self.dict['_phases'].append((name, optional))
        # add the function
        self.dict["test_" + name] = test_func
        self.dict["__" + name] = _phase
        self.dict[name] = phase

    def Type(self):
        if hasattr(self.Type.im_func, 'type') == False:
            class mybase(object):

                def __init__(self, env):
                    if __debug__:
                        logInstanceCreation(self)
                    self.passed = False  # this allow us to skip tests if we have stacked decorators
                    self.env = env
                    for p in self._phases:
                        setattr(self, "func_" + p[0], [])

                def isSet(self):
                    for p in self._phases:
                        # we want to find a phase that was set
                        if getattr(self, "func_" + p[0], []) != []:
                            return True
                    return False

                def isValid(self):
                    for p in self._phases:
                        # if value not set and it is not option
                        if getattr(self, "func_" + p[0], []) == [] and p[1] == False:
                            return False
                    return True

                def FoundPhases(self):
                    ret = []
                    for p in self._phases:
                        # we want phases that are called
                        if getattr(self, "func_" + p[0], []) != []:
                            ret.append(p[0])
                    return ret

                def RequiredPhases(self):
                    ret = []
                    for p in self._phases:
                        # we want items that are not options
                        if p[1] == False:
                            ret.append(p[0])
                    return ret

            self.Type.im_func.type = mybase.__class__('%sSectionType' % self.name, (mybase,), self.dict)

        return self.Type.im_func.type

    def GetHandler(self):
        return self.processfunc

    def HandleConcept(self, name):
        if name in self.concepts:
            return True
        return False
