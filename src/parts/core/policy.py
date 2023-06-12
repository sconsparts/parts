
import parts.api as api
# clean up more...


class Policy:
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


class SCMPolicy(Policy):
    warning = 1
    error = 2
    update = 3


api.register.add_global_parts_object("ReportingPolicy", ReportingPolicy)
api.register.add_global_object("ReportingPolicy", ReportingPolicy)

api.register.add_global_parts_object("REQPolicy", REQPolicy)
api.register.add_global_object("REQPolicy", REQPolicy)

api.register.add_global_parts_object("SCMPolicy", SCMPolicy)
api.register.add_global_object("SCMPolicy", SCMPolicy)
