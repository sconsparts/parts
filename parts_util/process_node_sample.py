# This is an example of node processing for each part in product. "processNode()"
# should be changed according to user's needs. Main stuff is in process_node_ifc.py
# and in process_nodes.py.

import process_node_ifc

class SampleNodeCallback(process_node_ifc.NodeCallback):
    def __init__(self):
        process_node_ifc.NodeCallback.__init__(self)

    def processNode(self, nodeId, nodeDict, nodeObj):
        print 'Processing "%s":' % nodeDict['partAlias']

def createNodeCallbackObject():
    return SampleNodeCallback()
