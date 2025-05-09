from pack_utils import PackScenario
from uvpm_core import (Stage,
                     PackTask,
                     StageParams,
                     StdStageTarget)


class Scenario(PackScenario):

    def run(self):

        task = PackTask(0, self.pack_params)

        stage_params = StageParams(self.cx.params)

        stage = Stage()
        stage.params = stage_params
        stage.target = self.op_target
        stage.input_islands = [self.islands_to_pack]
        stage.static_islands = self.static_islands

        self.add_stage_to_task(task, stage)
        self.pack_manager.add_task(task)

        return self.pack_manager.pack()
