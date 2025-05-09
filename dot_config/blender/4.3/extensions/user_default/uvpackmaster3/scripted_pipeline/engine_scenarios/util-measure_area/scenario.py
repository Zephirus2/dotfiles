from scripted_pipeline import GenericScenario
from uvpm_core import packer, RetCode, LogType
from utils import area_to_string


class Scenario(GenericScenario):

    def run(self):

        if self.cx.params['merged']:
            merged_island = self.cx.selected_islands.merge()
            area = merged_island.area()
            msg = "Selected islands merged area: {}".format(area_to_string(area))
        else:
            area = self.cx.selected_islands.area()
            msg = "Selected islands area: {}".format(area_to_string(area))

        packer.send_log(LogType.STATUS, msg)
        return RetCode.SUCCESS
