import nox


#@nox.session
#def lint(session):
    #'''Run Lint checks'''
    #session.install('pylint')
    #session.run("pylint","--rcfile=setup.cfg","src/parts","-j8")

@nox.session(python=['3.11','3.12','3.13','3.14','3.15'])
def autests(session):
    '''Run AuTests'''
    session.install('autest')
    session.install("-e",".")
    session.run("autest","-D","tests/gold_tests","--sandbox", f"_sandbox/{session.python}")