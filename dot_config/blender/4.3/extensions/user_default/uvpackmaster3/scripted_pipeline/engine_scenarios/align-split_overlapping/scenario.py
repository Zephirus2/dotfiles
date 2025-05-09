from similarity_utils import SimilarityScenario
from uvpm_core import packer, RetCode, LogType, IslandSet, OverlapDetectionMode, InputError
from utils import eprint, flag_islands
from scripted_pipeline import extract_param

import math


class SplitMetadata:
    def __init__(self, x_tile):
        self.split_offset = (0, 0)
        self.processed = False
        self.x_tile = x_tile


class Scenario(SimilarityScenario):

    def run(self):
        
        detection_mode = extract_param(OverlapDetectionMode, self.cx.params['split_overlap_detection_mode'])
        max_tile_x = self.cx.params['split_overlap_max_tile_x']
        
        iparam_names = (self.cx.params['split_offset_x_iparam_name'], self.cx.params['split_offset_y_iparam_name'])
        iparam_descriptors = tuple(self.iparams_manager.iparam_desc(name) for name in iparam_names)

        align_priority_iparam_desc = self.simi_params.align_priority_iparam_desc

        sort_by_overlapping_count = lambda island: len(island.overlapping)
        sort_by_align_priority = lambda island: -island.get_iparam(align_priority_iparam_desc)
        
        if align_priority_iparam_desc:
            sort_key = lambda island: (sort_by_align_priority(island), sort_by_overlapping_count(island))
        else:
            sort_key = sort_by_overlapping_count

        offset_step = 1

        exceeding_x_tile = IslandSet()
        processed = IslandSet()
        to_process = self.cx.selected_islands.clone()

        for island in to_process:

            x_tile = None
            if max_tile_x > 0:
                bbox = island.bbox()

                max_x = bbox.max_corner.x
                if max_x >= max_tile_x or max_x < 0.0:
                    exceeding_x_tile.append(island)

                x_tile = int(max_x)

            island.metadata = SplitMetadata(x_tile)

        if len(exceeding_x_tile) > 0:
            flag_islands(to_process, exceeding_x_tile)
            raise InputError("Some UVs have the X coord lower than 0 or greater than the 'Max Tile (X)' value: {}. The problematic islands were selected. Aborting.".format(max_tile_x))
        
        def free_to_split_offset_delta(island, free_offset):
            if max_tile_x <= 0:
                return (free_offset, 0)

            y_offset = 0

            metadata = island.metadata
            orig_x_tile = metadata.x_tile

            assert orig_x_tile < max_tile_x
            x_offset = orig_x_tile + free_offset

            while x_offset >= max_tile_x:
                x_offset -= max_tile_x
                y_offset += 1

            metadata.x_tile = x_offset
            x_offset -= orig_x_tile

            return (x_offset, y_offset)


        while len(to_process) > 0:
            to_check = to_process.clone()
            to_check += processed

            o_map = to_check.overlapping_map(detection_mode)
            # eprint(o_map)
            overlapping_islands = []
            for island in to_check:
                island.overlapping = o_map[island]

                if len(island.overlapping) == 0:
                    if not island.metadata.processed:
                        island.metadata.processed = True
                        processed.append(island)
                    continue

                if island.metadata.processed:
                    island.metadata.local_offset = 0
                    continue
            
                island.metadata.local_offset = None
                overlapping_islands.append(island)

            overlapping_islands.sort(key=sort_key)
            to_process.clear()

            for island in overlapping_islands:

                free_offset = None
                offset_to_check = 0

                while True:
                    offset_found = True

                    for other_island in island.overlapping:
                        if other_island.metadata.local_offset is not None and other_island.metadata.local_offset == offset_to_check:
                            offset_found = False
                            break

                    if offset_found:
                        free_offset = offset_to_check
                        break

                    offset_to_check += offset_step

                split_offset_delta = free_to_split_offset_delta(island, free_offset)
                split_offset = island.metadata.split_offset

                island.metadata.local_offset = free_offset
                island.metadata.split_offset = tuple(split_offset[c] + split_offset_delta[c] for c in range(len(split_offset)))

                if free_offset != 0:
                    to_process.append(island.offset(split_offset_delta[0], split_offset_delta[1]))
                else:
                    to_process.append(island)

        assert(len(processed) == len(self.cx.selected_islands))

        moved_count = 0

        for island in processed:
            split_offset = island.metadata.split_offset

            if split_offset[0] != 0 or split_offset[1] != 0:
                moved_count += 1

            for c in range(len(split_offset)):
                island.set_iparam(iparam_descriptors[c], split_offset[c])
            
        for desc in iparam_descriptors:
            desc.mark_dirty()

        packer.send_out_islands(processed, send_transform=True, send_iparams=True)
        packer.send_log(LogType.STATUS, "Done. Islands moved: {}".format(moved_count))
        return RetCode.SUCCESS
