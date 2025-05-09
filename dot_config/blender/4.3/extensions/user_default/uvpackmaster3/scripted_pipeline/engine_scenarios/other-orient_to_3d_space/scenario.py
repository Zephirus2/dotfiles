from scripted_pipeline import GenericScenario, extract_param
from uvpm_core import packer, RetCode, LogType, Axis, CoordSpace
from utils import eprint

class Scenario(GenericScenario):

    def run(self):

        self.send_tip('if you are getting unstable results when orienting islands, make sure the UV map has no N-gons')
        packer.send_log(LogType.STATUS, "Orienting islands...")

        prim_3d_axis = extract_param(Axis, self.cx.params['prim_3d_axis'])
        prim_uv_axis = extract_param(Axis, self.cx.params['prim_uv_axis'])
        sec_3d_axis = extract_param(Axis, self.cx.params['sec_3d_axis'])
        sec_uv_axis = extract_param(Axis, self.cx.params['sec_uv_axis'])
        axes_space = extract_param(CoordSpace, self.cx.params['axes_space'])
        prim_sec_bias = self.cx.params['prim_sec_bias']

        oriented_islands = self.cx.selected_islands.orient_to_3d_space(
            prim_3d_axis,
            prim_uv_axis,
            sec_3d_axis,
            sec_uv_axis,
            axes_space,
            prim_sec_bias)

        packer.send_out_islands(oriented_islands, send_transform=True)
        packer.send_log(LogType.STATUS, "Done. Islands oriented: {}".format(len(oriented_islands)))
        return RetCode.SUCCESS
