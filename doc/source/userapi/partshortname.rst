.. py:function:: PartShortName()

    Returns the short name of the parts.
    This generally only makes sense in the case of a sub parts in which you want to get the name value of the Parts without the parent value.
    If this a top level Part the return value of this function and the return value of PartName() will be equal

    :return: The short name of the Part
    :rtype: str