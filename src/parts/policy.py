

# clean up more...


class Policy(object):
    pass


class ReportingPolicy(Policy):
    ignore = 0
    verbose = 1
    message = 2
    warning = 3
    error = 4


class REQPolicy(Policy):
    ignore = 0
    verbose = 1
    warning = 3
    error = 4


class VCSPolicy(Policy):
    warning = 1
    error = 2
    update = 3
