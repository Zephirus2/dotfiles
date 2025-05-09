

from .operator_box import *
from .grouping_scheme_access import GroupingSchemeAccess
from .utils import get_prefs, PanelUtilsMixin

class BoxEditUI(PanelUtilsMixin):

    def __init__(self, context, scene_props):

        self.prefs = get_prefs()
        self.init_access(context, ui_drawing=True)
        self.context = context
        self.scene_props = scene_props

    def impl_force_show_coords(self):

        return False
    
    def impl_init_operator(self, op):
        pass

    def draw(self, layout):

        col = layout.column(align=True)
        edit_enable = self.impl_edit_enable()
        active_box = self.impl_active_box()
        draw_box_coords = active_box is not None and (edit_enable or self.impl_force_show_coords())

        if edit_enable or draw_box_coords:
            edit_box = col.box()
            edit_col = edit_box.column(align=True)
            # edit_col.enabled = edit_enable

        if draw_box_coords:
            edit_col.label(text='Box coordinates:')

            coord_c = edit_col.column(align=True)

            row = coord_c.row(align=True)
            row.prop(active_box, "p1_x")

            row = coord_c.row(align=True)
            row.prop(active_box, "p1_y")

            row = coord_c.row(align=True)
            row.prop(active_box, "p2_x")

            row = coord_c.row(align=True)
            row.prop(active_box, "p2_y")

            edit_col.separator()

        if edit_enable:
            edit_box = col.box()
            edit_col = edit_box.column(align=True)
            
            row = edit_col.row(align=True)
            op = row.operator(self.impl_set_to_tile_operator().bl_idname)
            self.impl_init_operator(op)

            edit_col.separator()
            edit_col.label(text='Islands inside the box:')

            select_op = self.impl_select_islands_in_box_operator()
            row = edit_col.row(align=True)
            op = row.operator(select_op.bl_idname, text="Select")
            self.impl_init_operator(op)
            op.select = True

            op = row.operator(select_op.bl_idname, text="Deselect")
            self.impl_init_operator(op)
            op.select = False

            box = edit_col.box()
            box.prop(self.scene_props, "fully_inside")

            edit_col.separator()
            edit_col.label(text='Move the box to an adjacent tile:')

            move_op = self.impl_move_box_operator()

            move_cols = self.create_split_columns(edit_col, (0.33, 0.33))

            op = move_cols[0].operator(move_op.bl_idname, text="↖")
            self.impl_init_operator(op)
            op.dir_x = -1
            op.dir_y = 1
            op = move_cols[0].operator(move_op.bl_idname, text="←")
            self.impl_init_operator(op)
            op.dir_x = -1
            op.dir_y = 0
            op = move_cols[0].operator(move_op.bl_idname, text="↙")
            self.impl_init_operator(op)
            op.dir_x = -1
            op.dir_y = -1

            op = move_cols[1].operator(move_op.bl_idname, text="↑")
            self.impl_init_operator(op)
            op.dir_x = 0
            op.dir_y = 1
            move_cols[1].label(text=" ")
            op = move_cols[1].operator(move_op.bl_idname, text="↓")
            self.impl_init_operator(op)
            op.dir_x = 0
            op.dir_y = -1

            op = move_cols[2].operator(move_op.bl_idname, text="↗")
            self.impl_init_operator(op)
            op.dir_x = 1
            op.dir_y = 1
            op = move_cols[2].operator(move_op.bl_idname, text="→")
            self.impl_init_operator(op)
            op.dir_x = 1
            op.dir_y = 0
            op = move_cols[2].operator(move_op.bl_idname, text="↘")
            self.impl_init_operator(op)
            op.dir_x = 1
            op.dir_y = -1

            box = edit_col.box()
            box.label(text='TIP: press with Shift to move the box')
            box.label(text='together with selected islands inside')

            edit_col.separator()

        if edit_enable:
            col.operator(UVPM3_OT_FinishBoxRendering.bl_idname)
        else:
            op = col.operator(self.impl_render_boxes_operator().bl_idname)
            self.impl_init_operator(op)


class GroupingSchemeBoxesEditUI(GroupingSchemeAccess, BoxEditUI):

    def __init__(self, context, scene_props, access_desc_id):
        self.access_desc_id = access_desc_id
        super().__init__(context, scene_props)

    def impl_edit_enable(self):

        return self.prefs.group_scheme_boxes_editing

    def impl_set_to_tile_operator(self):

        return UVPM3_OT_SetGroupingSchemeBoxToTile

    def impl_render_boxes_operator(self):

        return UVPM3_OT_RenderGroupingSchemeBoxes

    def impl_move_box_operator(self):

        return UVPM3_OT_MoveGroupingSchemeBox

    def impl_select_islands_in_box_operator(self):

        return UVPM3_OT_SelectIslandsInGroupingSchemeBox
    
    def impl_init_operator(self, op):

        op.access_desc_id = self.access_desc_id



class CustomTargetBoxEditUI(BoxEditUI, CustomTargetBoxAccess):

    def impl_force_show_coords(self):

        return True

    def impl_edit_enable(self):

        return self.prefs.custom_target_box_editing

    def impl_set_to_tile_operator(self):

        return UVPM3_OT_SetCustomTargetBoxToTile

    def impl_render_boxes_operator(self):

        return UVPM3_OT_RenderCustomTargetBox

    def impl_move_box_operator(self):

        return UVPM3_OT_MoveCustomTargetBox

    def impl_select_islands_in_box_operator(self):

        return UVPM3_OT_SelectIslandsInCustomTargetBox
