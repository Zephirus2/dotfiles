# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
from . import module_loader
module_loader.unload_uvpm3_modules(locals())

bl_info = {
    "name": "UVPackmaster3",
    "author": "glukoz",
    "version": (3, 3, 3),
    "blender": (4, 0, 0),
    "location": "UV Editor -> N panel -> UVPackmaster3",
    "description": "",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "UV"}

from .app_iface import *

if INSIDE_BLENDER:
    from .operator import *
    from .operator_islands import *
    from .operator_box import *
    from .operator_misc import *
    from .panel import *
    from .panel_align import *
    from .prefs import *
    from .register_utils import *
    from .presets import *
    from .presets_grouping_scheme import *
    from .mode import *
    from .grouping import *
    from .group import *
    from .grouping_scheme import *
    from .grouping_scheme_ui import *
    from .multi_panel import *
    from .multi_panel_manager import *
    from .help import *
    from .scripting import *
    from .debug import *
    from .scripted_pipeline.modes.pack_modes import UVPM3_PT_OverrideGlobalOptionsPopover

    from .scripted_pipeline import panels
    scripted_panels_modules = module_loader.import_submodules(panels)
    scripted_panels_classes = module_loader.get_registrable_classes(scripted_panels_modules, sub_class=UVPM3_PT_Registerable)
    scripted_panels_classes.sort(key=lambda x: x.PANEL_PRIORITY)

    from .scripted_pipeline import operators
    scripted_operators_modules = module_loader.import_submodules(operators)
    scripted_operators_classes = module_loader.get_registrable_classes(scripted_operators_modules, sub_class=UVPM3_OT_Generic)

    from .scripted_pipeline import modes
    scripted_modes_modules = module_loader.import_submodules(modes)
    scripted_modes_classes = module_loader.get_registrable_classes(scripted_modes_modules,
                                                                   sub_class=UVPM3_Mode_Generic, required_vars=("MODE_ID",))
    scripted_modes_classes.sort(key=lambda x: x.MODE_PRIORITY)


    classes = (
        UVPM3_UL_GroupInfo,
        UVPM3_UL_TargetBoxes,
        UVPM3_MT_BrowseGroupingSchemesDefault,
        UVPM3_MT_BrowseGroupingSchemesEditor,
        UVPM3_MT_BrowseGroupingSchemesLockGroup,
        UVPM3_MT_BrowseGroupingSchemesStackGroup,
        UVPM3_MT_BrowseGroupingSchemesTrackGroup,
        UVPM3_MT_BrowseGroupingSchemesContext,
        UVPM3_OT_BrowseGroupingSchemes,

        UVPM3_PackStrategyProps,

        UVPM3_Box,
        UVPM3_GroupOverrides,
        UVPM3_GroupInfo,
        UVPM3_GroupingOptionsBase,
        UVPM3_GroupingOptions,
        UVPM3_AutoGroupingOptions,
        UVPM3_GroupingScheme,

        UVPM3_GroupingSchemeAccessDescriptor,
        UVPM3_GroupingSchemeAccessDescriptorContainer,

        UVPM3_NumberedGroupsDescriptor,
        UVPM3_NumberedGroupsDescriptorContainer,

        UVPM3_TrackGroupsProps,

        UVPM3_DeviceSettings,
        UVPM3_SavedDeviceSettings,
        UVPM3_Preferences,

        UVPM3_OT_Debug,
        UVPM3_OT_DismissWarning,

        UVPM3_MT_BrowseModes,
        UVPM3_OT_SelectMode,

        UVPM3_OT_ShowHideAdvancedOptions,
        UVPM3_OT_SetEnginePath,
        UVPM3_OT_AdjustIslandsToTexture,
        UVPM3_OT_UndoIslandsAdjustemntToTexture,

        UVPM3_OT_Help,
        UVPM3_OT_MainModeHelp,
        UVPM3_OT_SetupHelp,

        UVPM3_OT_HelpPopup,
        UVPM3_OT_WarningPopup,

        UVPM3_OT_StdShowIParam,
        UVPM3_OT_StdSetIParam,
        UVPM3_OT_StdResetIParam,

        UVPM3_OT_ShowManualGroupIParam,
        UVPM3_OT_SetManualGroupIParam,
        UVPM3_OT_ResetManualGroupIParam,
        UVPM3_OT_SelectManualGroupIParam,
        UVPM3_OT_ApplyGroupingToScheme,

        UVPM3_OT_NumberedGroupShowIParam,
        UVPM3_OT_NumberedGroupSetIParam,
        UVPM3_OT_NumberedGroupSetFreeIParam,
        UVPM3_OT_NumberedGroupResetIParam,
        UVPM3_OT_NumberedGroupSelectIParam,
        UVPM3_OT_NumberedGroupSelectNonDefaultIParam,

        UVPM3_OT_FinishBoxRendering,
        
        UVPM3_OT_RenderGroupingSchemeBoxes,
        UVPM3_OT_SetGroupingSchemeBoxToTile,
        UVPM3_OT_MoveGroupingSchemeBox,

        UVPM3_OT_SelectIslandsInGroupingSchemeBox,
        UVPM3_OT_SelectIslandsInCustomTargetBox,

        UVPM3_OT_RenderCustomTargetBox,
        UVPM3_OT_SetCustomTargetBoxToTile,
        UVPM3_OT_MoveCustomTargetBox,

        UVPM3_PT_Presets,
        UVPM3_PT_PresetsCustomTargetBox,
        UVPM3_PT_PresetsGroupingSchemeDefault,
        UVPM3_PT_PresetsGroupingSchemeEditor,
        UVPM3_OT_SavePreset,
        UVPM3_OT_SaveGroupingSchemePreset,
        UVPM3_OT_RemovePreset,
        UVPM3_OT_LoadPreset,
        UVPM3_OT_LoadTargetBox,
        UVPM3_OT_LoadGroupingSchemePreset,
        UVPM3_OT_ResetToDefaults,

        UVPM3_PT_OverrideGlobalOptionsPopover,

        UVPM3_OT_NewGroupingScheme,
        UVPM3_OT_RemoveGroupingScheme,
        UVPM3_OT_NewGroupInfo,
        UVPM3_OT_RemoveGroupInfo,
        UVPM3_OT_MoveGroupInfo,
        UVPM3_OT_NewTargetBox,
        UVPM3_OT_RemoveTargetBox,
        UVPM3_OT_MoveTargetBox,

        UVPM3_OT_SetRotStepScene,
        UVPM3_MT_SetRotStepScene,
        UVPM3_OT_SetRotStepGroup,
        UVPM3_MT_SetRotStepGroup,

        UVPM3_OT_SetPixelMarginTexSizeScene,
        UVPM3_MT_SetPixelMarginTexSizeScene,
        UVPM3_OT_SetPixelMarginTexSizeGroup,
        UVPM3_MT_SetPixelMarginTexSizeGroup,

        UVPM3_ScriptEntry,
        UVPM3_ScriptCollection,
        UVPM3_ScriptContainer,
        UVPM3_Scripting,
        UVPM3_OT_ScriptSet,
        UVPM3_MT_ScriptSet,
        UVPM3_UL_ScriptCollection,

        UVPM3_OT_ScriptAddEntry,
        UVPM3_OT_ScriptRemoveEntry,
        UVPM3_OT_ScriptMoveActiveEntry,
        UVPM3_OT_ScriptAllowExecution,

        UVPM3_PT_MultiPanels,
        UVPM3_OT_SelectMultiPanel,
        UVPM3_OT_ExpandPanel,

        UVPM3_MultiPanelSettings,
        UVPM3_SavedMultiPanelSettings,

        UVPM3_PanelSettings,
        UVPM3_SavedPanelSettings,

        UVPM3_ScriptedPipelineProperties,
        UVPM3_SceneProps
    )


    def register():
        AppInterface.register(classes, scripted_operators_classes)
        register_modes(scripted_modes_classes)
        register_specific()

    def unregister():
        AppInterface.unregister()
