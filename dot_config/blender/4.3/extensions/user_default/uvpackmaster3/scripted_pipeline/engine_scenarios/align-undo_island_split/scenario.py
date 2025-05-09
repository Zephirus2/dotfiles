from scripted_pipeline import GenericScenario
from uvpm_core import packer, RetCode, LogType, IslandSet, InputError
from utils import eprint


class Scenario(GenericScenario):

    def run(self):

        iparam_names = (self.cx.params['split_offset_x_iparam_name'], self.cx.params['split_offset_y_iparam_name'])
        iparam_descriptors = tuple(self.iparams_manager.iparam_desc(name) for name in iparam_names)

        processed = IslandSet()
        moved_count = 0

        for island in self.cx.selected_islands:

            split_offset = tuple(island.get_iparam(desc) for desc in iparam_descriptors)

            for c in range(len(split_offset)):
                if split_offset[c] == iparam_descriptors[c].default_value:
                    raise InputError("Split data not available for all selected islands")

            if split_offset[0] != 0 or split_offset[1] != 0:
                processed_island = island.offset(-split_offset[0], -split_offset[1])
                moved_count += 1
            else:
                processed_island = island

            for desc in iparam_descriptors:
                processed_island.set_iparam(desc, desc.default_value)
            processed.append(processed_island)
        
        for desc in iparam_descriptors:
            desc.mark_dirty()

        packer.send_out_islands(processed, send_transform=True, send_iparams=True)
        packer.send_log(LogType.STATUS, "Done. Islands moved: {}".format(moved_count))
        return RetCode.SUCCESS
