from .pack_context import PackContext
from .group import UVPM3_GroupInfo
from .grouping_scheme_access import GroupByNameAccess


class GroupMap:

    def __init__(self, g_scheme, p_context):

        self.g_scheme = g_scheme
        self.p_context = p_context

        self.group_name_access = GroupByNameAccess(g_scheme)
        self.map = [UVPM3_GroupInfo.DEFAULT_GROUP_NUM] * self.p_context.total_face_count

        self.init()

    def set_map(self, p_obj, loc_face_idx, group_num):

        self.map[p_obj.to_glob_face_idx(loc_face_idx)] = group_num

    def get_map(self, p_obj, loc_face_idx):

        group_num = self.map[p_obj.to_glob_face_idx(loc_face_idx)]
        # assert(group_num >= 0)
        return group_num

    def iparam_label(self):

        return 'Group'


class GroupMapMaterial(GroupMap):

    def init(self):

        for p_obj in self.p_context.p_objects:

            if len(p_obj.obj.material_slots) == 0:
                raise RuntimeError('Grouping by material error: object does not have a material assigned')

            faces_to_process = p_obj.get_selected_faces_stored()

            for face in faces_to_process:
                mat_idx = face.material_index

                if not (mat_idx >= 0 and mat_idx < len(p_obj.obj.material_slots)):
                    raise RuntimeError('Grouping by material error: invalid material id')

                mat = p_obj.obj.material_slots[mat_idx]

                if mat is None:
                    raise RuntimeError('Grouping by material error: some faces belong to an empty material slot')

                group = self.group_name_access.get(mat.name)
                self.set_map(p_obj, face.index, group.num)

    def iparam_label(self):

        return 'Group By Material'


class GroupMapMeshPart(GroupMap):

    def init(self):

        for p_obj in self.p_context.p_objects:

            faces_to_process = p_obj.get_selected_faces_stored()
            faces_left = set([face.index for face in faces_to_process])

            while len(faces_left) > 0:

                new_group = self.group_name_access.get("Mesh part {}".format(self.g_scheme.group_count()))

                face_idx = list(faces_left)[0]
                faces_left.remove(face_idx)

                faces_to_process = []
                faces_to_process.append(face_idx)

                while len(faces_to_process) > 0:

                    new_face_idx = faces_to_process[0]
                    del faces_to_process[0]

                    self.set_map(p_obj, new_face_idx, new_group.num)
                    new_face = p_obj.mw.faces[new_face_idx]

                    for vert in new_face.verts:
                        for face in vert.link_faces:
                            if face.index not in faces_left:
                                continue

                            faces_to_process.append(face.index)
                            faces_left.remove(face.index)

    def iparam_label(self):

        return 'Group By Mesh Part'

    
class GroupMapObject(GroupMap):

    def init(self):

        for p_obj in self.p_context.p_objects:
            group = self.group_name_access.get(p_obj.obj.name)

            faces_to_process = p_obj.get_selected_faces_stored()

            for face in faces_to_process:
                self.set_map(p_obj, face.index, group.num)

    def iparam_label(self):

        return 'Group By Object'


class GroupMapTile(GroupMap):

    def init(self):

        for p_obj in self.p_context.p_objects:

            faces_to_process = p_obj.get_selected_faces_stored()

            for face in faces_to_process:
                uvs = face.loops[0][p_obj.uv_layer].uv
                group = self.group_name_access.get("Tile {}:{}".format(int(uvs[0]), int(uvs[1])))
                self.set_map(p_obj, face.index, group.num)

    def iparam_label(self):

        return 'Group By Tile'


class GroupMapManual(GroupMap):

    def init(self):

        for p_obj in self.p_context.p_objects:

            vcolor_layer = p_obj.get_or_create_vcolor_layer(self.g_scheme.get_iparam_info())

            for face in p_obj.mw.faces:
                group_num = self.g_scheme.get_iparam_value(vcolor_layer, face)  
                self.set_map(p_obj, face.index, group_num)
