

from SCons.Executor import TSList, Executor
import parts.api as api


def def_TSList___iter__(klass):
    def __iter__(self):
        return self.func().__iter__()
    klass.__iter__ = __iter__


def_TSList___iter__(TSList)


def scan(self, scanner, node_list):
    """Scan a list of this Executor's files (targets or sources) for
    implicit dependencies and update all of the targets with them.
    This essentially short-circuits an N*M scan of the sources for
    each individual target, which is a hell of a lot more efficient.

    This function changes the core logic and depends on implicit values being cached
    It will scan the source/depends nodes as these are static in general, then scan for the 
    implicit targets. This is done to make sure dynamic items scan correctly as the process of being scanned
    my define values in the Environments being used. Failure to do this can lead to cases in which 
    values are missed and false rebuilds happen
    """
    env = self.get_build_env()
    path = self.get_build_scanner_path
    kw = self.get_kw()

    # we are scanning the node list.. which is either the target sources or the targets themselves.
    # either case the depends are added to the targets nodes
    # scan the node list, and store the results in a dict<node,[depends]>

    # this is the implicit depends of the executor itself (ie the action scanner)
    exec_depends = self.get_implicit_deps()

    # if this is target nodes.. scan the batch var targets and assign as we scan
    # the target case will only have the node show up once, so it is the easy and fast case
    # we do this check as the core scons does some stuff to "speed up" logic and cost of correctness
    # which breaks correctness with batch_key usage.
    if self.batches[0].targets[0] == node_list[0]:
        for batch in self.batches:
            for trg in batch.targets:
                api.output.verbose_msg(["node.scan", "node"], f"{trg} is being scanned. Results:")
                trg.disambiguate()
                # get the implicit depends after we scan the children of the
                deps = trg.get_implicit_deps(env, scanner, path, kw)
                trg.add_to_implicit(exec_depends+deps)
        return

    # the else case is we what source nodes. This case is more complex as the source for batches
    # can show up more than once for different targets. This is unlikely but possible.
    # in this case we have two concerns. The common case len(self.batches) == 1 and when it is
    # larger than 1 ( uncommon.. which is the case we are using batch_key in the actions )
    # the common case just scan the node list and assign all depends to all the targets
    # the batch_key case when we need to separate the depends to the correct target group list. 
    # The node list is a concat of the sources.
    # is it very unlikely we have any duplicates in the batches. If we do.. well bad things will
    # probably happen. We also don't want to add items to built targets as they are already built
    # as this can cause a crash in SCons as the executor of the target may be set to None

    depends_map = {}
    for batch in self.batches:
        # scan each node given we have not seen it yet
        # as scanning can take a long time
        deps = []
        for src in batch.sources:
            if id(src) not in depends_map:
                src.disambiguate()
                # we are here because we don't have implicit set yet
                depends_map[id(src)] = src.get_implicit_deps(env, scanner, path, kw)
            deps += depends_map[id(src)]

        deps.extend(exec_depends)

        for trg in batch.targets:
            trg.add_to_implicit(deps)

Executor.scan = scan


# vim: set et ts=4 sw=4 ai ft=python :
