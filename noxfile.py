import nox


#@nox.session
#def lint(session):
    #'''Run Lint checks'''
    #session.install('pylint')
    #session.run("pylint","--rcfile=setup.cfg","src/parts","-j8")

@nox.session(python=["3.6","3.7","3.8","3.9","3.10",'3.11'])
def autests(session):
    '''Run AuTests'''
    session.install('autest')
    session.install("-e",".")
    session.run("autest","-D","tests/gold_tests")