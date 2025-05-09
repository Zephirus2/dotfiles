# from scripted_pipeline import 
from pack_utils import PackScenario
from uvpm_core import (
                    packer,
                    PackTask,
                    ScaleMode,
                    InputError,
                    LogType)

from utils import eprint

from collections import namedtuple


class GroupCluster:

    def __init__(self):
        self.groups = []
        self.tdensity_cluster_ids = set()

    def add_group(self, group):
        self.groups.append(group)
        self.tdensity_cluster_ids.add(group.tdensity_cluster)
                
    def depends_on(self, other_group):
        if other_group.tdensity_cluster in self.tdensity_cluster_ids:
            return True

        for group in self.groups:
            if group.target.intersects(other_group.target):
                return True
            
        return False
    
    def merge(self, other):
        self.groups += other.groups
        self.tdensity_cluster_ids = self.tdensity_cluster_ids.union(other.tdensity_cluster_ids)
                

class Scenario(PackScenario):

    GROUP_AREA_TOLERANCE = 1e-5
    next_fixed_scale_cluster = 1000 * 1000

    def is_packed_with_fixed_scale(self, island):
        return self.g_scheme.is_packed_with_fixed_scale(island)

    def island_overlaps_op_target(self, island):
        for group in self.g_scheme.groups:
            if island.overlaps(group.target):
                return True
            
        return False

    def island_overlaps_op_target(self, island):
        for group in self.g_scheme.groups:
            if island.overlaps(group.target):
                return True
            
        return False

    def run(self):

        group_clusters = []

        TDensityClusterData = namedtuple('TDensityClusterData', ('group_name', 'scale_mode'))
        tdensity_clusters = dict()

        for group in self.g_scheme.groups:

            if group.islands is None:
                continue

            td_cluster = tdensity_clusters.get(group.tdensity_cluster)
            if td_cluster is None:
                tdensity_clusters[group.tdensity_cluster] = TDensityClusterData(group_name=group.name, scale_mode=group.scale_mode)
            
            else:
                if td_cluster.scale_mode != group.scale_mode:
                    packer.send_log(LogType.ERROR, "Inconsistent 'Scale Mode' setting for groups packed with uniform texel density")
                    packer.send_log(LogType.ERROR, "Groups with inconsistent setting: {}, {}".format(td_cluster.group_name, group.name))
                    raise InputError()

            target_indicies = []

            for idx, g_cluster in enumerate(group_clusters):
                if g_cluster.depends_on(group):
                    target_indicies.append(idx)
                    
            if len(target_indicies) == 0:
                target_indicies.append(len(group_clusters))
                group_clusters.append(GroupCluster())

            while len(target_indicies) > 1:
                group_clusters[target_indicies[0]].merge(group_clusters[target_indicies[-1]])
                del group_clusters[target_indicies[-1]]
                del target_indicies[-1]

            group_clusters[target_indicies[0]].add_group(group)

        # eprint('len(group_clusters): ' + str(len(group_clusters)))
        if len(group_clusters) == 0:
            raise InputError("No group found on input")

        for g_cluster in group_clusters:
            fixed_scale_cluster = None
            
            for group in g_cluster.groups:
                if group.scale_mode != ScaleMode.FIXED_SCALE:
                    continue

                if fixed_scale_cluster is None:
                    fixed_scale_cluster = self.next_fixed_scale_cluster
                    self.next_fixed_scale_cluster += 1

                g_cluster.tdensity_cluster_ids.discard(group.tdensity_cluster)
                group.tdensity_cluster = fixed_scale_cluster

            if fixed_scale_cluster is not None:
                g_cluster.tdensity_cluster_ids.add(fixed_scale_cluster)

            
        tdensity_tip_sent = False
        order_tip_sent = False

        for g_cluster in group_clusters:
            if not tdensity_tip_sent and (len(g_cluster.tdensity_cluster_ids) > 1):
                first_group = g_cluster.groups[0]
                second_group = None
                for group in g_cluster.groups[1:]:
                    if group.tdensity_cluster != first_group.tdensity_cluster:
                        second_group = group
                        break

                assert second_group is not None

                self.send_tip('note that packing two groups into the same UV space with independent texel density may significantly increase the packing time')
                self.send_tip('if the operation takes too long, consider packing with the same texel density')
                self.send_tip('groups packed with independent texel density: {}, {}'.format(first_group.name, second_group.name))
                tdensity_tip_sent = True

            task = PackTask(0, self.pack_params)
            sorted_groups = sorted(g_cluster.groups, key=lambda g: g.create_id)

            for idx, group in enumerate(sorted_groups):
                poly_array = group.target.to_poly_array()
                if not order_tip_sent:
                    for other_group in sorted_groups[0:idx]:
                        other_poly_array = other_group.target.to_poly_array()
                        if (poly_array.area() + self.GROUP_AREA_TOLERANCE) < other_poly_array.area() and poly_array.within(other_poly_array):
                            self.send_tip('packing coverage may not be optimal if a group with smaller target boxes is packed after a group with larger target boxes')
                            self.send_tip('consider changing the packing order - swap the following groups on the list: {}, {}'.format(other_group.name, group.name))
                            order_tip_sent = True
                            break

                stage = group.to_stage()
                stage.static_islands = self.static_islands
                self.add_stage_to_task(task, stage)

            self.pack_manager.add_task(task)

        return self.pack_manager.pack()
