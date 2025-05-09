from similarity_utils import SimilarityScenario
from uvpm_core import packer, RetCode, LogType, IslandSet
from utils import eprint


class SplitMetadata:
    def __init__(self):
        self.split_offset = 0
        self.processed = False


class Scenario(SimilarityScenario):

    MAX_GROUPS_EXCEEDED_ERROR_STR_ARRAY = [
        "Maximum number of groups exceeded",
        "Consider increasing the 'Minimum Group Size' value"
    ]

    def run(self):
        
        target_iparam_desc = self.iparams_manager.iparam_desc(self.cx.params['target_iparam_name'])
        min_group_size = self.cx.params['min_group_size']

        packer.send_log(LogType.STATUS, "Determining similarity groups...")

        input_islands = self.cx.input_islands
        simi_groups = input_islands.split_by_similarity(self.simi_params)

        group_num = target_iparam_desc.min_value

        if min_group_size > 1:
            idx = 0
            while idx < len(simi_groups):
                group = simi_groups[idx]

                if len(group) < min_group_size:
                    group.set_iparam(target_iparam_desc, group_num)
                    del simi_groups[idx]
                    continue

                idx += 1

        group_num += 1

        for group in simi_groups:
            if group_num > target_iparam_desc.max_value:
                for error_str in self.MAX_GROUPS_EXCEEDED_ERROR_STR_ARRAY:
                    packer.send_log(LogType.ERROR, error_str)
                return RetCode.INVALID_INPUT

            group.set_iparam(target_iparam_desc, group_num)
            group_num += 1

        target_iparam_desc.mark_dirty()
        packer.send_out_islands(input_islands, send_iparams=True)
        return RetCode.SUCCESS
