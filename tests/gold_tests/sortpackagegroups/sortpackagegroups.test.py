Test.Summary = '''
Testing env.GetPackageGroupFiles() function returns correct list of
installed files.
'''

Setup.Copy.FromDirectory('scons')

run0 = Test.AddBuildRun('pack0.txt LOGGER=TEXT_LOGGER')
run0.ReturnCode = 0
pack0txt = run0.Disk.File('pack0.txt')

import json


def contentCheck(data):
    gold = {
        'install/part1.txt': 'part1.txt',
        'install/part2.txt': 'part2.txt',
        'install/part3.txt': 'part3.txt',
    }
    if json.loads(data) != gold:
        return '{0} != {1}'.format(data, json.dumps(gold))
    return None
pack0txt.Exists = True
pack0txt.Content = Testers.FileContentCallback(
    callback=contentCheck,
    description='Checking pack0.txt contents'
)

copy1 = Test.AddTestRun('update_part1_txt', 'Updating part1.txt')
copy1.Command = 'echo 1part1.txt>part1.txt'

copy2 = Test.AddTestRun('update_part2_txt', 'Updating part2.txt')
copy2.Command = 'echo 2part2.txt>part2.txt'

run1 = Test.AddBuildRun(
    'build::name::pack0 --verbose=loading,node_check,update_check LOGGER=TEXT_LOGGER')
run1.ReturnCode = 0

alllog = run1.Disk.File('logs/all.log')
# comment out as the "cache logic" is being redone
# def pack0LogContent(data):
# if not "Verbose: [loading] reduced sections to process= [(['build::pack0'], None)]" in data:
# return "Section 'build::pack0' is not in reduced sections list:\n{0}".format(data)
#alllog.Exists = True
# alllog.Content = Testers.FileContentCallback(
# callback=pack0LogContent,
#description='Checking verbose stream content'
#)

pack1txt = run1.Disk.File('pack0.txt')


def content1Check(data):
    gold = {
        'install/part1.txt': '1part1.txt',
        'install/part2.txt': '2part2.txt',
        'install/part3.txt': 'part3.txt',
    }
    if json.loads(data) != gold:
        return '{0} != {1}'.format(data, json.dumps(gold))
    return None
pack1txt.Exists = True
pack1txt.Content = Testers.FileContentCallback(
    callback=content1Check,
    description='Checking pack0.txt contents after the second run'
)

# vim: set et ts=4 sw=4 ai ft=python :
