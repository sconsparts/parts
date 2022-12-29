# this overide deals with Part providing better information for what there is a duplicated
# target/environment/builder being reproted by SCons. This allows Part to report which two
# Parts are the issues, which helps a lot when this happens across parts, as the SCons
# message is hard to deal with by default and it does not know of "part/components"
# We also make what Component "owns" these node for faster checks latter.

import parts.common as common
import parts.api as api
import parts.errors as errors
import parts.glb as glb
import parts.metatag as metatag
import SCons.Builder
import time

scons_node_errors = SCons.Builder._node_errors


def parts_node_errors(builder, env, tlist, slist):
    """SCons errors out without a lot of useful info
    This function tries to do the same tests, but report more useful stuff given that we have components
    """

    #print("source:", [str(i) for i in slist])
    #print("target:", [str(i) for i in tlist])
    section = glb.engine._part_manager.section_from_env(env)

    if section:
        tag_part_info(tlist + slist, section.Part)
        # add the node to known targets or sources or the given section
        section.Targets.update(tlist)
        section.Sources.update(slist)
        def_phase = section.DefiningPhase

        if def_phase:
            # store the item with the phase only
            section.GroupedTargets.setdefault(def_phase, set()).update(tlist)
            section.GroupedSources.setdefault(def_phase, set()).update(slist)

    # check to see if we have allow duplicates defined
    # if so we need to see if we have a duplicate defined as known
    
    if env.get('allow_duplicates'):
        if section is not None:
            pname = section.Part.Name
        else:
            pname = None
        key = f"{[n.ID for n in tlist]} {builder.get_name(env)} {pname} {[n.ID for n in slist]}"
        # make sure we can record that nodes before we stop SCons registering the values here
        # we throw an exception to allow Parts to handle the allow_duplicate feature for all builders
        if key in glb.known_dups:
            raise errors.AllowedDuplication(tlist)
        else:
            glb.known_dups[key]=tlist

    error = False
    warn = False
    # use basic SCons template for how it handles these error.. may append on to later
    for t in tlist:
        if t.side_effect:
            error = True
        if t.has_explicit_builder():
            if (t.env is not None and t.env is not env and
                    # Check OverrideEnvironment case - no error if wrapped Environments
                    # are the same instance, and overrides lists match
                    not (getattr(t.env, '__subject', 0) is getattr(env, '__subject', 1) and
                         getattr(t.env, 'overrides', 0) == getattr(env, 'overrides', 1) and
                         not builder.multi)):
                action = t.builder.action
                t_contents = action.get_contents(tlist, slist, t.env)
                contents = action.get_contents(tlist, slist, env)
                if t_contents == contents:
                    warn = True
                else:
                    error = True
            if builder.multi:
                if t.get_executor() is None:
                    api.output.warning_msg(
                        f"Executor is None for node '{t.ID}'.\n"
                        " This is a sign that there is a order dependency that is incorrect in the mutli builder"
                        " used to generate this target", 
                        show_stack=False
                    )
                    del t.executor
                if t.get_executor() and (t.builder != builder or t.get_executor().get_all_targets() != tlist):
                    error = True
            elif t.sources != slist:
                error = True

        if error:
            tenv = {} if t.env is None else t.env
            api.output.error_msg(
                f'{t} is ambiguous because it is defined with two different Environments\n One environment was defined in Part "'
                f'{tenv.get("PART_ALIAS", "<unknown>")}"\n'
                f'The other was defined in Part "{env.get("PART_ALIAS", "<unknown>")}"',
                show_stack=False,
                exit=False
            )
        elif warn:
            api.output.warning_msg(
                'Build issue found with two different Environments\n'
                f' One environment was defined in Part "{t.env.get("PART_ALIAS", "<unknown>")}"\n'
                f' The other was defined in Part "{env.get("PART_ALIAS", "<unknown>")}"',
                show_stack=False
            )

    # call the SCons code
    scons_node_errors(builder, env, tlist, slist)


SCons.Builder._node_errors = parts_node_errors

# util function


def tag_part_info(node_list, pobj):
    '''
    Tags the node with information we will want to have stored for fast loads later
    This functions will tag each node with the component sections that it is a part of
    It will also tag the directory of the node with this information as well.

    NOte this is not used at the moment as I have to reimple the stored cache info    
    '''
    api.output.verbose_msg(["partinfo"],f"Tagging {node_list} nodes with info of part defining them")
    st=time.time()
    for node in node_list:

        # tag the node with sections that it is a part of.
        alias = pobj.Alias
        section = pobj.DefiningSection

        # get meta node info
        data = metatag.MetaTagValue(node, 'components', ns='partinfo', default={})
        # Tag this node with information about the Parts and Section that would care about it
        # ideally the section should be enough to do fileters on.
        data.setdefault(alias, set()).add(section)
        # Store the info
        metatag.MetaTag(node, 'partinfo', components=data)

        # Tag Parent Directory nodes
        # only do this if the current node is a file/diretory type node
        if isinstance(node, SCons.Node.FS.Base):
            if isinstance(node, SCons.Node.FS.Entry):
                dnode = node.get_dir()
            else:
                dnode = node.Dir('.')

            # go up the directory chain and set values
            # This allows for directory node targets to know what set of sections/parts have to be
            # loaded
            while True:
                data = metatag.MetaTagValue(dnode, 'components', ns='partinfo', default={})
                sections = data.setdefault(alias, set())
                # we do this check as the directory chain may be long and there is a high
                # chance that this information is already set on the directory node.
                # if that is the case, all the parents have been set as well. so we we can
                # just break out of the loop
                if section in sections:
                    break
                sections.add(section)

                # should be check to see if we are at the top
                if dnode == dnode.Dir('..'):
                    break
                dnode = dnode.Dir('..')
    api.output.verbose_msg(['partinfo'],f"Tag time: {time.time()-st}")
