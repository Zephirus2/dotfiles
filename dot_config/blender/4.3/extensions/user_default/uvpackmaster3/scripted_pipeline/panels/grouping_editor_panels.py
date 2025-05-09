from ...panel_grouping_editor import UVPM3_PT_GenericGroupingEditor, UVPM3_PT_GroupTargetBoxes, UVPM3_PT_Grouping, UVPM3_PT_SchemeGroups


class UVPM3_PT_GroupingEditor(UVPM3_PT_Grouping, UVPM3_PT_GenericGroupingEditor):

    bl_idname = 'UVPM3_PT_GroupingEditor'
    bl_label = 'Grouping Editor'


class UVPM3_PT_SchemeGroupsGroupingEditor(UVPM3_PT_SchemeGroups, UVPM3_PT_GenericGroupingEditor):

    bl_idname = 'UVPM3_PT_SchemeGroupsGroupingEditor'
    bl_parent_id = UVPM3_PT_GroupingEditor.bl_idname


class UVPM3_PT_GroupTargetBoxesGroupingEditor(UVPM3_PT_GroupTargetBoxes, UVPM3_PT_GenericGroupingEditor):

    bl_idname = 'UVPM3_PT_GroupTargetBoxesGroupingEditor'
    bl_parent_id = UVPM3_PT_GroupingEditor.bl_idname
    