from uvpm_core import (
                    packer,
                    Island,
                    SimilarityParams,
                    IslandSet,
                    PackRunConfig,
                    PackParams,
                    PixelPerfectVertAlignMode,
                    RetCode,
                    Matrix3x3,
                    OverlapDetectionMode,
                    LogType,
                    IslandFlag,
                    solution_available,
                    append_ret_codes,
                    SimilarityMode,
                    CoordSpace,
                    InputError,
                    ScaleMode,
                    fixed_scale_enabled,
                    StdStageTarget,
                    raise_InvalidTopologyExtendedError)

from scripted_pipeline import extract_param, GenericScenario, Struct
from similarity_utils import SimilarityScenario
from utils import flag_islands, box_from_coords, eprint, area_to_string, split_islands

from .pack_manager import PackManager


class PackOpType:

    PACK = 0
    PACK_TO_OTHERS = 1
    REPACK_WITH_OTHERS = 2

    @classmethod
    def static_islands_enable(cls, op_type):
        return (op_type == cls.PACK_TO_OTHERS) or (op_type == cls.REPACK_WITH_OTHERS)


OVERLAPPING_WARNING_MSG_ARRAY = [
    "Overlapping islands were detected after packing (check the selected islands).",
    "Consider increasing the 'Precision' parameter."
]

OUTSIDE_TARGET_BOX_WARNING_MSG = "Some islands are outside their target boxes after packing (check the selected islands)."
NO_SIUTABLE_DEVICE_STATUS_MSG = "No suitable packing device."

NO_SIUTABLE_DEVICE_ERROR_MSG_ARRAY = [
    "No suitable packing device to perform the operation.",
    "Make sure that you have at least one packing device enabled in Preferences."
]

CORRECT_VERTICES_WARNING_MSG_ARRAY = [
    "Similarity option Correct Vertices is ignored when packing with stack groups.",
    "Read stack groups documentation for more info."
]


def merge_overlapping_islands(input_islands, overlapping_mode, iparam_desc):

    if overlapping_mode == OverlapDetectionMode.DISABLED and iparam_desc is None:
        return input_islands

    overlapping_groups, not_overlapping_islands = input_islands.split_by_overlapping(overlapping_mode, iparam_desc)
    output_islands = IslandSet()

    for group in overlapping_groups:
        output_islands.append(group.merge())

    output_islands += not_overlapping_islands
    return output_islands


class Tracker:

    def __init__(self, raw_tracker):
        self.tracker_island = raw_tracker[0]
        self.transform = raw_tracker[1]
        self.transform_inverse = raw_tracker[2]


class PackScenario(GenericScenario):

    MAX_ISLAND_DIM_ALLOWED = 4.0

    GROUP_TOGETHER_HEURISTIC_WARNING_SENT = False
    GROUP_TOGETHER_HEURISTIC_WARNINGS = [
        "Packing groups together requires heuristic search enabled to produce the optimal result",
        "It is strongly recommended to enable heuristic search when using this mode"
    ]

    PIXEL_PERFECT_ALIGN_TIP = 'there are certain restrictions of the Pixel Perfect Alignment option - press the help button next to the option to learn more'

    def __init__(self, cx):
        super().__init__(cx)

        self.simi_scenario = None
        if 'simi_params' in self.cx.params:
            self.simi_scenario = SimilarityScenario(self.cx)

        self.tracker_data = None

    def island_overlaps_op_target(self, island):
        return island.overlaps(self.op_target)

    def add_stage_to_task(self, task, stage):
        cls = type(self)

        if (not cls.GROUP_TOGETHER_HEURISTIC_WARNING_SENT) and\
           (not self.pack_manager.runconfig.heuristic_search_enabled()):
            
            try:
                groups_together = stage.params.groups_together
            except:
                groups_together = task.params.groups_together

            if groups_together:
                for warn in cls.GROUP_TOGETHER_HEURISTIC_WARNINGS:
                    packer.send_log(LogType.WARNING, warn)
                cls.GROUP_TOGETHER_HEURISTIC_WARNING_SENT = True

        task.add_stage(stage)

    def apply_pack_ratio_to_islands(self, islands):

        if self.pack_ratio == 1.0:
            return islands

        output = IslandSet()

        for island in islands:
            output.append(island.scale(self.pack_ratio, 1.0))

        return output

    def unapply_pack_ratio_from_islands(self, islands):

        if self.pack_ratio == 1.0:
            return islands

        output = IslandSet()

        for island in islands:
            output.append(island.scale(1.0 / self.pack_ratio, 1.0))

        return output

    def process_driver_island(self, island, combined_transform, transformed_tracker_islands):
        island_transform = island.transform()
        combined_transform_local = combined_transform * island_transform

        for driver_island in island.parents:
            self.process_driver_island(driver_island, combined_transform_local, transformed_tracker_islands)
            driver_trackers = self.tracker_data.get(driver_island)

            if driver_trackers is None:
                continue

            for tracker in driver_trackers:
                tracker_transform = tracker.transform_inverse * combined_transform_local * tracker.transform
                transformed_tracker_islands.append(Island(tracker.tracker_island, tracker_transform))

    def send_out_islands(self, island_set_list, **kwargs):

        if self.tracker_data is not None:
            transformed_tracker_islands = IslandSet()

            for islands in island_set_list:
                if islands is None:
                    continue

                for island in islands:
                    self.process_driver_island(island, Matrix3x3.identity(), transformed_tracker_islands)

            island_set_list.append(transformed_tracker_islands)

        transform_kw = 'send_transform'
        if (self.pixel_perfect_vert_align_mode != PixelPerfectVertAlignMode.NONE) and (transform_kw in kwargs) and kwargs[transform_kw]:
            pixel_perfect_aligned = False
            aligned_set = IslandSet()

            for islands in island_set_list:
                if islands is None:
                    continue

                for island in islands:
                    pack_data = island.pack_data
                    stage_params = pack_data.stage_params

                    if not stage_params.pixel_perfect_align_enabled:
                        continue

                    unmerged = island.unmerge()
                    for unmerged_island in unmerged:
                        aligned_set.append(unmerged_island.pixel_perfect_align(pack_data.target_box, stage_params.pixel_margin_tex_size, self.pixel_perfect_vert_align_mode))

                    pixel_perfect_aligned = True

            if pixel_perfect_aligned:
                del kwargs[transform_kw]
                transform_kw = 'send_vertices'
                kwargs[transform_kw] = True

                island_set_list = [aligned_set]

        if self.pack_ratio != 1.0 and (transform_kw in kwargs) and kwargs[transform_kw]:
            tmp_list = []

            for islands in island_set_list:
                if islands is None:
                    continue
                tmp_list.append(self.unapply_pack_ratio_from_islands(islands))

            island_set_list = tmp_list

        packer.send_out_islands(island_set_list, **kwargs)

    def is_packed_with_fixed_scale(self, island):
        return fixed_scale_enabled(self.scale_mode)

    def split_islands_by_fixed_scale(self, islands):
        fixed_islands = IslandSet()
        non_fixed_islands = IslandSet()

        for island in islands:
            (fixed_islands if self.is_packed_with_fixed_scale(island) else non_fixed_islands).append(island)

        return fixed_islands, non_fixed_islands
    
    def apply_max_dimension_limit(self, islands):
        max_dim = islands.max_island_dimension()

        if max_dim <= self.MAX_ISLAND_DIM_ALLOWED:
            return islands

        fixed_islands, non_fixed_islands = self.split_islands_by_fixed_scale(islands)

        max_dim = non_fixed_islands.max_island_dimension()

        if max_dim <= self.MAX_ISLAND_DIM_ALLOWED:
            return islands
        

        scale_factor = self.MAX_ISLAND_DIM_ALLOWED / max_dim
        non_fixed_islands = non_fixed_islands.scale(scale_factor, scale_factor)

        fixed_islands += non_fixed_islands
        return fixed_islands
    
    def normalize_scale(self, islands):

        normalize_scale_iparam_desc = None
        normalize_multiplier_iparam_name = self.cx.params['normalize_multiplier_iparam_name']

        if normalize_multiplier_iparam_name is not None:
            normalize_scale_iparam_desc = self.iparams_manager.iparam_desc(normalize_multiplier_iparam_name)

        fixed_islands, non_fixed_islands = self.split_islands_by_fixed_scale(islands)

        if len(non_fixed_islands) == 0:
            return fixed_islands

        non_fixed_islands = non_fixed_islands.normalize(extract_param(CoordSpace, self.cx.params['normalize_space']), normalize_scale_iparam_desc)
        fixed_islands += non_fixed_islands
        return fixed_islands

    def pre_run(self):

        pack_op_type = self.cx.params['pack_op_type']

        if self.simi_scenario:
            self.simi_scenario.pre_run()

        self.scale_mode = extract_param(ScaleMode, self.cx.params.get('scale_mode'))
        self.pack_params = PackParams(self.cx.params)

        if self.cx.params.get('pixel_perfect_align'):
            self.pixel_perfect_vert_align_mode = extract_param(PixelPerfectVertAlignMode, self.cx.params['pixel_perfect_vert_align_mode'])
            self.send_tip(self.PIXEL_PERFECT_ALIGN_TIP)
        else:
            self.pixel_perfect_vert_align_mode = PixelPerfectVertAlignMode.NONE

        self.op_target = None
        in_target_boxes = self.cx.params['target_boxes']

        if in_target_boxes is not None:
            self.op_target = self.in_boxes_to_target(in_target_boxes)

        selected_islands = self.apply_pack_ratio_to_islands(self.cx.selected_islands)
        unselected_islands = self.apply_pack_ratio_to_islands(self.cx.unselected_islands)
        pinned_islands = self.apply_pack_ratio_to_islands(self.cx.pinned_islands)

        normalize_scale = self.cx.params['normalize_scale']

        if pack_op_type == PackOpType.REPACK_WITH_OTHERS:
            if not normalize_scale:
                self.send_tip("consider enabling 'Normalize Scale' in order to keep the scale of selected and unselected islands consistent during repacking")

            overlapping, not_overlapping = split_islands(unselected_islands, lambda i: self.island_overlaps_op_target(i))

            selected_islands += overlapping
            unselected_islands = not_overlapping
            
        selected_islands = self.apply_max_dimension_limit(selected_islands)

        self.pack_runconfig = PackRunConfig()
        self.pack_runconfig.asyn = True
        self.pack_runconfig.realtime_solution = True

        if 'heuristic_search_time' in self.cx.params:
            self.pack_runconfig.heuristic_search_time = self.cx.params['heuristic_search_time']
        if 'advanced_heuristic' in self.cx.params:
            self.pack_runconfig.advanced_heuristic = self.cx.params['advanced_heuristic']
        if 'heuristic_max_wait_time' in self.cx.params:
            self.pack_runconfig.heuristic_max_wait_time = self.cx.params['heuristic_max_wait_time']
        if 'heuristic_allow_mixed_scales' in self.cx.params:
            self.pack_runconfig.heuristic_allow_mixed_scales = self.cx.params['heuristic_allow_mixed_scales']

        self.islands_to_pack = selected_islands

        ### Lock params
        lock_group_iparam_desc = None
        lock_group_iparam_name = self.cx.params['lock_group_iparam_name']
        if lock_group_iparam_name is not None:
            lock_group_iparam_desc = self.iparams_manager.iparam_desc(lock_group_iparam_name)

        lock_overlapping_mode = extract_param(OverlapDetectionMode, self.cx.params['lock_overlapping_mode'], OverlapDetectionMode.DISABLED)
        locking_enabled = (lock_overlapping_mode != OverlapDetectionMode.DISABLED) or (lock_group_iparam_desc is not None)

        ### Track Groups
        track_group_iparam_desc = None
        track_group_iparam_name = self.cx.params['track_group_iparam_name']

        if track_group_iparam_name is not None:
            packer.send_log(LogType.STATUS, "Determining island trackers...")
            track_groups_props = Struct(self.cx.params['track_groups_props'])
            matching_mode = extract_param(SimilarityMode, track_groups_props.matching_mode)

            track_group_iparam_desc = self.iparams_manager.iparam_desc(track_group_iparam_name)
            tracker_islands = IslandSet()
            unselected_islands_tmp = IslandSet()

            for island in unselected_islands:
                target_list = unselected_islands_tmp if island.get_iparam(track_group_iparam_desc) == track_group_iparam_desc.default_value else tracker_islands
                target_list.append(island)

            unselected_islands = unselected_islands_tmp

            if locking_enabled:
                pre_lock_tracker_count = len(tracker_islands)
                tracker_islands = merge_overlapping_islands(tracker_islands, lock_overlapping_mode, lock_group_iparam_desc)

                if (pre_lock_tracker_count != len(tracker_islands)) and (matching_mode != SimilarityMode.BORDER_SHAPE):
                    raise InputError("Locking tracker islands is only supported when 'Matching Mode' is set to 'Border Shape'")

            self.tracker_data = dict()
            track_simi_params = SimilarityParams()

            track_simi_params.mode = matching_mode
            track_simi_params.threshold = 0.55
            track_simi_params.precision = 5000
            track_simi_params.check_holes = True
            track_simi_params.vertex_threshold = 0.005

            if SimilarityScenario.is_vertex_based_impl(matching_mode):
                SimilarityScenario(self.cx).send_vertex_based_tip('for track groups')

            driver_groups = self.islands_to_pack.split_by_iparam(track_group_iparam_desc)
            tracker_groups = tracker_islands.split_by_iparam(track_group_iparam_desc)
            non_tracker_total = IslandSet()

            if track_groups_props.require_match_for_all:
                non_matched_total = IslandSet()

            for g_num, driver_group in driver_groups.items():
                if g_num == track_group_iparam_desc.default_value:
                    continue
                
                tracker_group = tracker_groups.get(g_num)
                if tracker_group is None:
                    if track_groups_props.require_match_for_all:
                        non_matched_total += driver_group

                    continue

                del tracker_groups[g_num]

                trackers, non_tracker, non_matched = driver_group.find_trackers(track_simi_params, tracker_group)
                non_tracker_total += non_tracker

                if track_groups_props.require_match_for_all:
                    non_matched_total += non_matched

                for driver_island, raw_trackers in trackers.items():
                    self.tracker_data[driver_island] = [Tracker(raw_tracker) for raw_tracker in raw_trackers]

            for g_num, group in tracker_groups.items():
                if g_num == track_group_iparam_desc.default_value:
                    continue

                non_tracker_total += group

            if track_groups_props.require_match_for_all and len(non_matched_total) > 0:
                flag_islands(self.cx.input_islands, non_matched_total)
                packer.send_log(LogType.ERROR, "Could not find tracker islands for some driver islands (driver islands with no match were selected). Aborting")
                packer.send_log(LogType.ERROR, "You can ignore this error by disabling the 'Require Match For All' option")
                raise InputError()

            if len(non_tracker_total) > 0:
                flag_islands(self.cx.input_islands, non_tracker_total)
                packer.send_log(LogType.ERROR, "Could not find driver islands for some tracker islands (tracker islands with no match were selected). Aborting")
                packer.send_log(LogType.ERROR, "You can ignore this error by hiding the tracker islands with no match before packing")
                raise InputError()

        if PackOpType.static_islands_enable(pack_op_type):
            self.static_islands = unselected_islands.clone()

            if self.cx.params['pinned_as_others']:
                self.static_islands += pinned_islands

        else:
            self.static_islands = None

        ### Lock and stack groups
        if self.simi_scenario and self.simi_scenario.stack_group_iparam_desc:
            packer.send_log(LogType.STATUS, "Stack groups aligning...")

            if self.simi_scenario.is_vertex_based() and self.simi_scenario.simi_params.correct_vertices:
                for msg in CORRECT_VERTICES_WARNING_MSG_ARRAY:
                    packer.send_log(LogType.WARNING, msg)

                self.simi_scenario.simi_params.correct_vertices = False

            (aligned_groups, non_aligned_islands) = self.simi_scenario.align_similar_by_stack_group(self.islands_to_pack)

            AUX_LOCK_IPARAM_NAME = '__aux_lock_group'
            AUX_LOCK_IPARAM_LABEL = 'Aux Lock Group'
            AUX_LOCK_IPARAM_MIN_VALUE = self.simi_scenario.stack_group_iparam_desc.min_value
            AUX_LOCK_IPARAM_MAX_VALUE = 1000
            AUX_LOCK_IPARAM_DEF_VALUE = self.simi_scenario.stack_group_iparam_desc.default_value

            assert(AUX_LOCK_IPARAM_MAX_VALUE >= self.simi_scenario.stack_group_iparam_desc.max_value)

            aux_lock_group_iparam_desc = self.iparams_manager.register_iparam(
                AUX_LOCK_IPARAM_NAME,
                AUX_LOCK_IPARAM_LABEL,
                AUX_LOCK_IPARAM_MIN_VALUE,
                AUX_LOCK_IPARAM_MAX_VALUE,
                AUX_LOCK_IPARAM_DEF_VALUE
            )

            lock_groups = None
            if lock_group_iparam_desc:
                assert(aux_lock_group_iparam_desc.min_value == lock_group_iparam_desc.min_value)
                assert(aux_lock_group_iparam_desc.default_value == lock_group_iparam_desc.default_value)
                assert(aux_lock_group_iparam_desc.max_value >= lock_group_iparam_desc.max_value)

                lock_groups = self.islands_to_pack.split_by_iparam(lock_group_iparam_desc)

            curr_lock_val = aux_lock_group_iparam_desc.max_value

            for group in aligned_groups:

                while lock_groups and (curr_lock_val in lock_groups):
                    curr_lock_val -= 1
                    
                if curr_lock_val <= aux_lock_group_iparam_desc.default_value:
                        raise RuntimeError('Not enough lock groups')

                group.set_iparam(aux_lock_group_iparam_desc, curr_lock_val)
                curr_lock_val -= 1

            if lock_group_iparam_desc:
                non_aligned_islands.copy_iparam(aux_lock_group_iparam_desc, lock_group_iparam_desc)

            self.islands_to_pack = non_aligned_islands
            for group in aligned_groups:
                self.islands_to_pack += group

            lock_group_iparam_desc = aux_lock_group_iparam_desc
            locking_enabled = True

        if locking_enabled:
            self.islands_to_pack = merge_overlapping_islands(self.islands_to_pack, lock_overlapping_mode, lock_group_iparam_desc)

        if normalize_scale:
            self.islands_to_pack = self.normalize_scale(self.islands_to_pack)

        if self.g_scheme is not None:
            self.g_scheme.assign_islands_to_groups(self.islands_to_pack)

            if locking_enabled:
                self.g_scheme.validate_locking()

        rotation_step_iparam_name = self.cx.params['rotation_step_iparam_name']
        if rotation_step_iparam_name is not None:
            self.pack_params.rotation_step_iparam_desc = self.iparams_manager.iparam_desc(rotation_step_iparam_name)

        self.pack_manager = PackManager(self, self.pack_runconfig)

    def post_run_island_sets(self):

        return [self.pack_manager.packed_islands], self.pack_manager.invalid_islands


    def post_run(self, ret_code):

        packed_islands_array, invalid_islands = self.post_run_island_sets()

        if ret_code == RetCode.NO_SIUTABLE_DEVICE:
            packer.send_log(LogType.STATUS, NO_SIUTABLE_DEVICE_STATUS_MSG)
            for msg in NO_SIUTABLE_DEVICE_ERROR_MSG_ARRAY:
                packer.send_log(LogType.ERROR, msg)
            return ret_code

        if ret_code == RetCode.INVALID_ISLANDS:
            assert len(invalid_islands) > 0
            raise_InvalidTopologyExtendedError(invalid_islands)

        if not solution_available(ret_code):
            return ret_code

        packed_islands_area = 0.0
        for packed_islands in packed_islands_array:
            packed_islands_area += packed_islands.area()

        if ret_code == RetCode.SUCCESS:
            packer.send_log(LogType.STATUS, 'Packing done')
            packer.send_log(LogType.INFO, 'Packed islands area: {}'.format(area_to_string(packed_islands_area)))

        elif ret_code == RetCode.NO_SPACE:
            packer.send_log(LogType.STATUS, 'Packing stopped - no space to pack all islands')
            packer.send_log(LogType.WARNING, 'No space to pack all islands')
            packer.send_log(LogType.WARNING, 'Overlap check was performed only on the islands which have been packed')
        
        else:
            assert(False)

        if self.pack_runconfig.heuristic_search_time < 0:
            self.send_tip("if you want to improve the packing result, consider enabling 'Heuristic Search'")

        overlapping = IslandSet()

        for packed_islands in packed_islands_array:
            packed_overlapping = packed_islands.overlapping_islands(packed_islands)[0]
            packed_overlapping.set_flags(IslandFlag.OVERLAPS)
            overlapping += packed_overlapping

            if self.static_islands is not None:
                packed_static_overlapping = packed_islands.overlapping_islands(self.static_islands)[0]
                packed_static_overlapping.set_flags(IslandFlag.OVERLAPS)
                overlapping += packed_static_overlapping

        flagged_islands = overlapping
        flag_islands(self.cx.selected_islands, flagged_islands)

        if len(overlapping) > 0:
            for msg in OVERLAPPING_WARNING_MSG_ARRAY:
                packer.send_log(LogType.WARNING, msg)

            ret_code = append_ret_codes(ret_code, RetCode.WARNING)

        return ret_code
