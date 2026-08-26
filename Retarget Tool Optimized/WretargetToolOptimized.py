# -*- coding: utf-8 -*-
"""W Retarget Tool Optimized.

UI 注释版：界面布局说明集中在 RetargetTool._build_ui 和 _add_row。

Run this file inside Maya's Script Editor.  It is deliberately standalone and
does not modify either of the original tools.

这是一个矩阵动画重定向工具，支持：
1. 批量重定向
2. 批量导出
3. 批量保存映射
4. 批量加载映射
5. 批量自动匹配
6. 批量匹配初始姿势
7. 批量选择候选骨骼
8. 批量应用候选骨骼
9. 批量取消选中
10. 批量删除行
11. 批量添加行
12. 批量清除行
13. 批量清除候选骨骼
14. 批量清除映射
15. 批量选择所有行
"""
from __future__ import print_function

import os
import time
import json
import difflib
import io

import maya.cmds as cmds
import maya.mel as mel


WINDOW_NAME = "WRetargetToolOptimized"
HELP_WINDOW_NAME = "WRetargetToolOptimizedHelp"
ATTRIBUTES = ("tx", "ty", "tz", "rx", "ry", "rz")


class RetargetTool(object):
    """Matrix based, non-destructive animation retargeting UI."""

    def __init__(self):
        # 初始化映射数据、UI 控件引用和运行状态
        self.rows = []
        self.cancel_requested = False
        self.progress = None
        self.status = None
        self.start_field = None
        self.end_field = None
        self.key_all_field = None
        self.match_root_translation_field = None
        self.key_bind_pose_field = None
        self.source_root_field = None
        self.target_root_field = None
        self.name_rules_field = None
        self.candidate_list = None
        self.candidates = []
        self.fuzzy_threshold_field = None
        self.export_path_field = None
        self._build_ui()

    def _build_ui(self):
        # ==================== 主窗口 ====================
        # 修改窗口初始大小可调整 widthHeight；窗口名称不要重复，否则 Maya
        # 会删除旧窗口后重新创建。
        if cmds.window(WINDOW_NAME, exists=True):
            cmds.deleteUI(WINDOW_NAME)

        window = cmds.window(WINDOW_NAME, title="动画重定向工具 - 优化版",
                             sizeable=True, widthHeight=(600, 650),
                             minimizeButton=True, maximizeButton=False,)
        # 主容器使用滚动布局，窄屏和大量映射行时仍可操作。
        self.main_scroll = cmds.scrollLayout(childResizable=True,
                                              horizontalScrollBarThickness=12,
                                              verticalScrollBarThickness=14,
                                              minChildWidth=480)
        self.main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        cmds.text(label="动画重定向工具 - 优化版",
                  align="left", height=25,
                  font="boldLabelFont",
                  backgroundColor=(0.12, 0.16, 0.22))
        cmds.text(label="矩阵动画重定向 · 骨骼映射 · FBX 导出————by:hanan",
                  align="left", height=18,
                  enable=False)
        # 顶部工具栏：把高频的说明、预设和界面操作集中到一处。
        self.toolbar = cmds.frameLayout(label="工具栏", collapsable=False,
                                        marginWidth=3, marginHeight=2,
                                        backgroundColor=(0.16, 0.18, 0.22))
        cmds.rowLayout(numberOfColumns=6, adjustableColumn=1,
                       columnWidth=[(1, 100), (2, 100), (3, 100),
                                    (4, 100), (5, 100), (6, 100)])
        cmds.button(label="使用说明", width=100, height=24, command=lambda *_: self.show_help())
        cmds.button(label="保存映射预设", width=100, height=24, command=lambda *_: self.save_mapping_preset())
        cmds.button(label="载入映射预设", width=100, height=24, command=lambda *_: self.load_mapping_preset())
        cmds.button(label="清空手动映射", width=100, height=24, command=lambda *_: self._clear_rows())
        cmds.button(label="移除空行", width=100, height=24, command=lambda *_: self._remove_empty_rows())
        cmds.button(label="清除候选", width=100, height=24, command=lambda *_: self._clear_candidates())
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.text(label="矩阵动画重定向：源对象与目标对象应在起始帧保持相同的绑定／初始姿势",
                  align="left")
        cmds.button(label="打开使用说明", width=100, height=24, command=lambda *_: self.show_help())

        # ==================== 步骤 1：帧范围 ====================
        # frameLayout 是可折叠的父容器；修改 collapse=True 可让它默认收起。
        self.range_frame = cmds.frameLayout(label="步骤 1：动画范围与烘焙选项",
                                             collapsable=True, collapse=False,
                                             marginWidth=0, marginHeight=0,
                                             backgroundColor=(0.18, 0.22, 0.28))
        # rowLayout 按列排列控件。columnWidth5 中的数字依次对应 5 列宽度；
        # 如果某列太宽会产生空隙，太窄则会遮挡文字。
        cmds.text(label="开始帧_必须设置为初始姿势所在的那一帧",width=80,align="center",backgroundColor=(0.5, 0.5, 0.0),height=24,wordWrap=True,recomputeSize=False,)
        cmds.rowLayout(numberOfColumns=5, adjustableColumn=5,
                       columnWidth5=(80, 80, 80, 80, 80),
                       columnAttach=[(1, "both", 0), (2, "both", 0),
                                     (3, "both", 0), (4, "both", 0),
                                     (5, "both", 0)])
        cmds.text(label="帧范围",width=80,align="center",backgroundColor=(0.0, 0.0, 0.1),height=24,wordWrap=True,recomputeSize=False,)
        self.start_field = cmds.intFieldGrp(label="开始", numberOfFields=1, value1=0,
                                             columnWidth2=(35, 35),backgroundColor=(0.266667, 0.266667, 0.266667),)
        self.end_field = cmds.intFieldGrp(label="结束", numberOfFields=1, value1=20,
                                           columnWidth2=(35, 35),backgroundColor=(0.266667, 0.266667, 0.266667),)
        self.key_all_field = cmds.checkBox(label="逐帧烘焙", value=True,width=80,height=24,backgroundColor=(0.266667, 0.266667, 0.266667),align="center",)
        cmds.button(label="新增映射行", command=lambda *_: self._add_row(),width=120,height=24,align="center")
        cmds.setParent("..")
        cmds.text(label="初始姿势自动匹配不好用，最好手动调节，让目标骨骼和源骨骼动作接近一致",width=80,align="center",backgroundColor=(0.5, 0.5, 0.0),height=24,wordWrap=True,recomputeSize=False,)
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=3,
                       columnWidth3=(160, 160, 80),
                       columnAttach=[(1, "both", 0), (2, "both", 0),
                                     (3, "both", 0)])
        self.match_root_translation_field = cmds.checkBox(label="同步映射根节点的位置", value=False,width=160,height=24,backgroundColor=(0.266667, 0.266667, 0.266667),align="center",)
        self.key_bind_pose_field = cmds.checkBox(label="在开始帧写入姿势关键帧", value=True,width=160,height=24,backgroundColor=(0.266667, 0.266667, 0.266667),align="center",)
        cmds.button(label="目标匹配源初始姿势", backgroundColor=(0.35, 0.60, 0.85),
                    command=lambda *_: self.match_initial_pose(),width=120,height=24,align="center")
        cmds.setParent("..")
        cmds.setParent("..")

        # ==================== 步骤 2：快速映射 ====================
        self.quick_frame = cmds.frameLayout(label="步骤 2：快速建立骨骼映射",
                                             collapsable=True, collapse=False,
                                             marginWidth=0, marginHeight=0,
                                             backgroundColor=(0.20, 0.25, 0.30))
        cmds.rowLayout(numberOfColumns=6, adjustableColumn=6,
                       columnWidth=[(1, 80), (2, 80), (3, 80),
                                    (4, 80), (5, 80), (6, 80)],
                       columnAttach=[(1, "both", 0), (2, "both", 0),
                                     (3, "both", 0), (4, "both", 0),
                                     (5, "both", 0), (6, "both", 0)])
        cmds.text(label="源根",width=80,align="center",backgroundColor=(0.0, 0.0, 0.1),height=24,wordWrap=True,recomputeSize=False,)
        self.source_root_field = cmds.textField(width=80, height=24)
        cmds.button(label="设源根", command=lambda *_: self._set_selected(self.source_root_field),align="center")
        self.target_root_field = cmds.textField(placeholderText="目标骨架根节点")
        cmds.button(label="设目标根", command=lambda *_: self._set_selected(self.target_root_field),align="center")
        cmds.button(label="生成候选", backgroundColor=(0.55, 0.65, 0.85),
                    command=lambda *_: self.auto_match_hierarchies())
        cmds.setParent("..")
        cmds.setParent("..")

        # ==================== 步骤 3：候选确认 ====================
        self.candidate_frame = cmds.frameLayout(label="步骤 3：候选映射确认与预设",
                                                 collapsable=True, collapse=False,
                                                 marginWidth=0, marginHeight=0,
                                                 backgroundColor=(0.22, 0.26, 0.30))

        cmds.rowLayout(numberOfColumns=5, adjustableColumn=4,
                       columnWidth=[(1, 120), (2, 120), (3, 120), (4, 120), (5, 120)],
                       columnAttach=[(1, "both", 0), (2, "both", 0),
                                     (3, "both", 0), (4, "both", 0),
                                     (5, "both", 0)])
        cmds.text(label="替换规则",width=120,align="center",backgroundColor=(0.0, 0.0, 0.1),height=24,wordWrap=True,recomputeSize=False,)
        self.name_rules_field = cmds.textField(
            placeholderText="源名称替换为目标名称，例如：mixamorig:=;Left=L_;Right=R_")
        cmds.text(label="相似度",width=120,align="center",backgroundColor=(0.0, 0.0, 0.1),height=24,wordWrap=True,recomputeSize=False,)
        self.fuzzy_threshold_field = cmds.intField(value=72, minValue=50, maxValue=100)
        cmds.button(label="生成候选", command=lambda *_: self.auto_match_hierarchies())
        cmds.setParent("..")
        cmds.text(label="候选映射（可多选；请确认后再应用）", align="left")
        self.candidate_list = cmds.textScrollList(numberOfRows=4, height=120, 
                                                  allowMultiSelection=True,
                                                  selectCommand=lambda *_: self.select_candidate_bone("source"))
        cmds.rowLayout(numberOfColumns=4, adjustableColumn=2,
                       columnWidth4=(150, 150, 150, 150),
                       columnAttach=[(1, "both", 0), (2, "both", 0),
                                    (3, "both", 0), (4, "both", 0),
                                    (5, "both", 0)])
        cmds.text(label="匹配类型：", width=120,height=24,align="center",backgroundColor=(0.0, 0.0, 0.1),wordWrap=True,recomputeSize=False,)
        cmds.text(label="层级路径 / 唯一同名 / 相似名称", width=120,height=24, align="center", backgroundColor=(0.25, 0.35, 0.25),recomputeSize=True,)
        cmds.text(label="相似名称需人工确认", width=120,height=24, align="center", backgroundColor=(0.40, 0.32, 0.18))
        cmds.text(label="候选不会自动覆盖手动映射", width=120,height=24, align="center",backgroundColor=(0.0, 0.0, 0.1))
        cmds.setParent("..")
        cmds.rowLayout(numberOfColumns=6, adjustableColumn=4,
                       columnWidth6=(100, 100, 100, 100, 100, 100),
                       columnAttach=[(1, "both", 0), (2, "both", 0),
                                    (3, "both", 0), (4, "both", 0),
                                    (5, "both", 0)])
        cmds.button(label="选择源骨骼", command=lambda *_: self.select_candidate_bone("source"))
        cmds.button(label="选择目标骨骼", command=lambda *_: self.select_candidate_bone("target"))
        cmds.button(label="应用选中候选", command=lambda *_: self.apply_candidates(selected_only=True))
        cmds.button(label="应用全部候选", command=lambda *_: self.apply_candidates(selected_only=False))
        cmds.button(label="保存预设 JSON", command=lambda *_: self.save_mapping_preset())
        cmds.button(label="载入预设 JSON", command=lambda *_: self.load_mapping_preset())
        cmds.setParent("..")
        cmds.setParent("..")

        cmds.separator(style="in")
        # ==================== 步骤 4：手动映射 ====================
        self.mapping_frame = cmds.frameLayout(label="步骤 4：手动骨骼映射（点击名称可在场景中选中）",
                                               collapsable=True, collapse=False,
                                               marginWidth=0, marginHeight=0)
        self.mapping_scroll = cmds.scrollLayout(parent=self.mapping_frame,
                                                childResizable=True, height=165)
        self.mapping_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=2)
        for _ in range(3):
            self._add_row()
        # 关闭 scrollLayout、frameLayout 后，显式回到主容器；后续步骤不会嵌套进步骤 4。
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.setParent("..")
        # Explicitly return to the main column.  This prevents subsequent
        # execution/export frames from becoming children of step 4.
        cmds.setParent(self.main_layout)

        # ==================== 步骤 5：执行 ====================
        self.execute_frame = cmds.frameLayout(label="步骤 5：执行重定向",
                                               collapsable=True, collapse=False,
                                               marginWidth=0, marginHeight=0,
                                               backgroundColor=(0.20, 0.28, 0.22))
        cmds.rowLayout(numberOfColumns=4, adjustableColumn=2,
                       columnWidth4=(150, 150, 150, 150))
        cmds.button(label="移除空映射", width=150, height=24, command=lambda *_: self._remove_empty_rows())
        cmds.button(label="开始重定向", width=150, height=24,
                    backgroundColor=(0.30, 0.68, 0.32),
                    annotation="根据当前映射和帧范围执行动画重定向",
                    command=lambda *_: self.retarget_all())
        cmds.button(label="取消", width=150, height=24,
                    backgroundColor=(0.78, 0.40, 0.20),
                    command=lambda *_: self._request_cancel())
        cmds.button(label="清空映射", width=150, height=24, command=lambda *_: self._clear_rows())
        cmds.setParent("..")

        # Keep progress controls in a fixed-width row.  Long DAG paths in a
        # status label must not force Maya to resize the whole window.
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2,
                       columnWidth2=(100, 500),
                        columnAttach=[(1, "both", 0), (2, "both", 0)])
        cmds.text(label="执行进度",  width=120,height=24,align="center",backgroundColor=(0.0, 0.0, 0.1),wordWrap=True,recomputeSize=False,)
        self.progress = cmds.progressBar(maxValue=1)
        cmds.setParent("..")
        self.status = cmds.text(label="就绪", align="left")
        cmds.setParent("..")
        cmds.separator(style="in")

        # ==================== 步骤 6：导出 ====================
        self.export_frame = cmds.frameLayout(label="步骤 6：FBX 导出（可选）",
                                              collapsable=True, collapse=True,
                                              marginWidth=0, marginHeight=0,
                                              backgroundColor=(0.28, 0.24, 0.18))
        scene_path = cmds.file(query=True, sceneName=True) or ""
        default_path = os.path.dirname(scene_path) if scene_path else ""
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnWidth3=(120, 220, 110))
        cmds.text(label="FBX 输出文件夹", width=120,height=24,align="center",backgroundColor=(0.0, 0.0, 0.1),wordWrap=True,recomputeSize=False,)
        self.export_path_field = cmds.textField(text=default_path)
        cmds.button(label="选择...", command=lambda *_: self._choose_export_folder())
        cmds.setParent("..")
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2,
                       columnWidth2=(300, 300), columnAttach=[(1, "both", 0), (2, "both", 0)])
        cmds.button(label="将目标节点导出为 FBX", command=lambda *_: self.export_targets())
        cmds.text(label="仅导出映射中填写的目标节点", width=300,height=24,align="center",backgroundColor=(0.0, 0.0, 0.1),wordWrap=True,recomputeSize=False,)
        cmds.setParent("..")
        cmds.setParent("..")

        cmds.setParent("..")
        cmds.setParent("..")
        cmds.showWindow(window)
        cmds.window(window, edit=True, sizeable=True)

    def _add_row(self):
        # 手动映射的一行布局顺序：
        # [源标签] [源输入框] [选源] [目标输入框] [设目标]
        # [参考输入框] [设参考] [删]
        # 下面的 columnWidth 数组必须与这 8 列一一对应。
        # The generic columnWidth flag works across Maya releases and keeps
        # this dynamic mapping row within the fixed window width.
        row = cmds.rowLayout(parent=self.mapping_layout, numberOfColumns=8,
                             adjustableColumn=2,
                             height=24,
                             # 不设置 adjustableColumn，避免第 2 列被 Maya
                             # 自动拉伸，导致修改 columnWidth 后看不到变化。
                             columnWidth=[(1, 75), (2, 75), (3, 75),
                                          (4, 75), (5, 75), (6, 75),
                                          (7, 75), (8, 75)],
                             columnAttach=[(1, "both", 1), (2, "both", 1),
                                           (3, "both", 1), (4, "both", 1),
                                           (5, "both", 1), (6, "both", 1),
                                           (7, "both", 1), (8, "both", 1)])
        cmds.text(label="源骨骼",width=80,align="center",backgroundColor=(0.0, 0.0, 0.1),height=24,wordWrap=True,recomputeSize=False,)
        source = cmds.textField(enterCommand=lambda *_: self._select_field_node(source),
                                receiveFocusCommand=lambda *_: self._select_field_node(source))
        cmds.button(label="选源", command=lambda *_: self._set_selected(source))
        target = cmds.textField(placeholderText="目标对象",
                                enterCommand=lambda *_: self._select_field_node(target),
                                receiveFocusCommand=lambda *_: self._select_field_node(target))
        cmds.button(label="目标骨骼", command=lambda *_: self._set_selected(target))
        relative = cmds.textField(placeholderText="可选：相对参考对象",
                                  enterCommand=lambda *_: self._select_field_node(relative),
                                  receiveFocusCommand=lambda *_: self._select_field_node(relative))
        cmds.button(label="设参考", command=lambda *_: self._set_selected(relative))
        remove = cmds.button(label="删", command=lambda *_: self._delete_row(row))
        self.rows.append({"layout": row, "source": source, "target": target,
                          "relative": relative, "remove": remove})

    def _select_field_node(self, field):
        """Select the node named in a mapping text field when it receives focus."""
        if not cmds.control(field, exists=True):
            return
        value = cmds.textField(field, query=True, text=True).strip()
        if value and cmds.objExists(value):
            cmds.select(value, replace=True)

    def _delete_row(self, layout):
        self.rows = [row for row in self.rows if row["layout"] != layout]
        if cmds.control(layout, exists=True):
            cmds.deleteUI(layout)

    def _set_selected(self, field):
        selection = cmds.ls(selection=True, long=True) or []
        if not selection:
            cmds.warning("请先选择一个变换节点。")
            return
        cmds.textField(field, edit=True, text=self._display_node_name(selection[0]),
                       annotation=selection[0])

    @staticmethod
    def _field_value(field):
        """Read the full DAG path stored in annotation, falling back to text.

        Text fields intentionally show compact names; annotation preserves the
        unambiguous long name selected by the user or generated by auto-match.
        """
        text = cmds.textField(field, query=True, text=True).strip()
        annotation = cmds.textField(field, query=True, annotation=True).strip()
        if annotation and (text == RetargetTool._display_node_name(annotation) or
                            not text):
            return annotation
        return text

    def _clear_rows(self):
        for row in self.rows:
            for field in (row["source"], row["target"], row["relative"]):
                cmds.textField(field, edit=True, text="", annotation="")

    def _remove_empty_rows(self):
        for row in list(self.rows):
            if not self._field_value(row["source"]) and not self._field_value(row["target"]):
                self._delete_row(row["layout"])
        if not self.rows:
            self._add_row()

    @staticmethod
    def _node_name_without_namespace(node):
        return node.split(":")[-1]

    @classmethod
    def _display_node_name(cls, node):
        """Compact candidate text while retaining full DAG paths internally."""
        leaf = node.split("|")[-1]
        return cls._node_name_without_namespace(leaf)

    def _hierarchy_joint_map(self, root):
        """Return stable relative-name keys for a joint hierarchy."""
        root_path = (cmds.ls(root, long=True) or [root])[0]
        root_parts = [self._node_name_without_namespace(part)
                      for part in root_path.split("|") if part]
        nodes = cmds.listRelatives(root_path, allDescendents=True, fullPath=True,
                                  type="joint") or []
        if cmds.nodeType(root_path) == "joint":
            nodes.append(root_path)
        mapping = {}
        for node in nodes:
            parts = [self._node_name_without_namespace(part)
                     for part in node.split("|") if part]
            key = "|".join(parts[len(root_parts):]) or "__ROOT__"
            mapping[key] = node
        return mapping

    def _first_empty_row(self):
        for row in self.rows:
            source = self._field_value(row["source"])
            target = self._field_value(row["target"])
            if not source and not target:
                return row
        self._add_row()
        return self.rows[-1]

    def _parse_name_rules(self):
        """Parse source-to-target substitutions: ``Left=L_;Arm=upperArm``."""
        raw = cmds.textField(self.name_rules_field, query=True, text=True).strip()
        rules = []
        if not raw:
            return rules
        for item in raw.split(";"):
            if not item.strip():
                continue
            if "=" not in item:
                raise RuntimeError("名称规则格式无效：{0}。请使用 旧名称=新名称，并以 ; 分隔。".format(item))
            old, new = item.split("=", 1)
            old = old.strip()
            new = new.strip()
            if not old:
                raise RuntimeError("名称规则左侧不能为空。")
            rules.append((old, new))
        return rules

    @staticmethod
    def _apply_name_rules(value, rules):
        for old, new in rules:
            value = value.replace(old, new)
        return value

    @staticmethod
    def _name_side(name):
        """Return left/right when common rig naming markers are present."""
        lower = name.lower()
        if "left" in lower or "_l_" in lower or lower.startswith("l_") or lower.endswith("_l"):
            return "left"
        if "right" in lower or "_r_" in lower or lower.startswith("r_") or lower.endswith("_r"):
            return "right"
        return None

    @staticmethod
    def _similarity_name(name):
        """Normalise separators so Upper_Arm and upperArm compare sensibly."""
        return "".join(character for character in name.lower() if character.isalnum())

    def _fuzzy_pairs(self, sources, targets, rules, threshold):
        """Return mutual-best fuzzy pairs only, to avoid speculative matches."""
        source_best = {}
        target_best = {}
        for source in sources:
            source_leaf = self._node_name_without_namespace(source.split("|")[-1])
            translated = self._apply_name_rules(source_leaf, rules)
            source_side = self._name_side(translated)
            for target in targets:
                target_leaf = self._node_name_without_namespace(target.split("|")[-1])
                target_side = self._name_side(target_leaf)
                if source_side and target_side and source_side != target_side:
                    continue
                score = difflib.SequenceMatcher(
                    None, self._similarity_name(translated), self._similarity_name(target_leaf)).ratio()
                if score < threshold:
                    continue
                if score > source_best.get(source, (0, None))[0]:
                    source_best[source] = (score, target)
                if score > target_best.get(target, (0, None))[0]:
                    target_best[target] = (score, source)
        result = []
        for source, (score, target) in source_best.items():
            if target_best.get(target, (0, None))[1] == source:
                result.append((source, target, "相似名称", score))
        return result

    def _add_mapping_pairs(self, pairs):
        """Append pairs without replacing any complete manual mapping rows."""
        existing = set()
        for row in self.rows:
            source = self._field_value(row["source"])
            target = self._field_value(row["target"])
            if source and target:
                existing.add((source, target))
        added = 0
        for source, target in pairs:
            if (source, target) in existing:
                continue
            row = self._first_empty_row()
            cmds.textField(row["source"], edit=True, text=self._display_node_name(source),
                           annotation=source)
            cmds.textField(row["target"], edit=True, text=self._display_node_name(target),
                           annotation=target)
            existing.add((source, target))
            added += 1
        return added

    def auto_match_hierarchies(self):
        """Generate reviewable source-to-target joint mapping candidates."""
        source_root = cmds.textField(self.source_root_field, query=True, text=True).strip()
        target_root = cmds.textField(self.target_root_field, query=True, text=True).strip()
        if not source_root or not target_root:
            cmds.warning("请先设置源骨架根节点和目标骨架根节点。")
            return
        if not cmds.objExists(source_root) or not cmds.objExists(target_root):
            cmds.warning("源骨架根节点或目标骨架根节点不存在。")
            return

        try:
            rules = self._parse_name_rules()
        except RuntimeError as error:
            cmds.warning(str(error))
            return
        source_map = self._hierarchy_joint_map(source_root)
        target_map = self._hierarchy_joint_map(target_root)
        if not source_map or not target_map:
            cmds.warning("未在一个或两个根节点下找到 joint 骨骼。")
            return

        pairs = []
        matched_sources = set()
        matched_targets = set()
        # Exact relative hierarchy paths after source-to-target substitutions
        # are safest and take priority.
        for key, source in sorted(source_map.items()):
            translated_key = "|".join(self._apply_name_rules(part, rules)
                                      for part in key.split("|"))
            target = target_map.get(translated_key)
            if target:
                pairs.append((source, target, "层级路径", 1.0))
                matched_sources.add(source)
                matched_targets.add(target)

        # Fall back only when a remaining leaf name is unique on both sides.
        def unique_leaves(nodes):
            result = {}
            for node in nodes:
                leaf = self._node_name_without_namespace(node.split("|")[-1])
                result.setdefault(leaf, []).append(node)
            return result

        source_leaves = unique_leaves(set(source_map.values()) - matched_sources)
        target_leaves = unique_leaves(set(target_map.values()) - matched_targets)
        translated_source_leaves = {}
        for leaf, nodes in source_leaves.items():
            translated_source_leaves.setdefault(self._apply_name_rules(leaf, rules), []).extend(nodes)
        for leaf in sorted(set(translated_source_leaves) & set(target_leaves)):
            if len(translated_source_leaves[leaf]) == 1 and len(target_leaves[leaf]) == 1:
                pairs.append((translated_source_leaves[leaf][0], target_leaves[leaf][0], "唯一同名", 1.0))

        paired_sources = {source for source, _, _, _ in pairs}
        paired_targets = {target for _, target, _, _ in pairs}
        threshold = cmds.intField(self.fuzzy_threshold_field, query=True, value=True) / 100.0
        pairs.extend(self._fuzzy_pairs(set(source_map.values()) - paired_sources,
                                       set(target_map.values()) - paired_targets,
                                       rules, threshold))

        self.candidates = pairs
        # Reveal the review area only after candidates have been generated.
        cmds.frameLayout(self.candidate_frame, edit=True, collapse=False)
        cmds.textScrollList(self.candidate_list, edit=True, removeAll=True)
        for source, target, method, score in pairs:
            cmds.textScrollList(self.candidate_list, edit=True,
                                append="[{0}{1}] {2}  →  {3}".format(
                                    method, " {0:.0f}%".format(score * 100) if score < 1 else "",
                                    self._display_node_name(source),
                                    self._display_node_name(target)))
        unmatched_source = len(source_map) - len({source for source, _, _, _ in pairs})
        unmatched_target = len(target_map) - len({target for _, target, _, _ in pairs})
        cmds.text(self.status, edit=True,
                  label="已生成 {0} 组候选；源未匹配 {1} 个，目标未匹配 {2} 个。确认后点击应用。".format(
                      len(pairs), unmatched_source, unmatched_target))

    def apply_candidates(self, selected_only):
        if not self.candidates:
            cmds.warning("请先生成名称匹配候选。")
            return
        pairs = [(source, target) for source, target, _, _ in self.candidates]
        if selected_only:
            indices = cmds.textScrollList(self.candidate_list, query=True,
                                           selectIndexedItem=True) or []
            pairs = [(self.candidates[index - 1][0], self.candidates[index - 1][1])
                     for index in indices]
            if not pairs:
                cmds.warning("请至少选择一条候选映射，或使用“应用全部候选”。")
                return
        added = self._add_mapping_pairs(pairs)
        cmds.text(self.status, edit=True,
                  label="已添加 {0} 组映射；已有的手工映射不会被覆盖。".format(added))

    def _clear_candidates(self):
        """清除候选显示，不影响已经填写的手动映射。"""
        self.candidates = []
        if self.candidate_list and cmds.control(self.candidate_list, exists=True):
            cmds.textScrollList(self.candidate_list, edit=True, removeAll=True)
        if self.candidate_frame and cmds.control(self.candidate_frame, exists=True):
            cmds.frameLayout(self.candidate_frame, edit=True, collapse=True)
        if self.status and cmds.control(self.status, exists=True):
            cmds.text(self.status, edit=True, label="候选列表已清除；手动映射未改变。")

    def select_candidate_bone(self, side="source"):
        """Select the source or target node represented by the highlighted row."""
        if not self.candidates:
            return
        indices = cmds.textScrollList(self.candidate_list, query=True,
                                       selectIndexedItem=True) or []
        if not indices:
            return
        index = indices[0] - 1
        if index < 0 or index >= len(self.candidates):
            return
        node = self.candidates[index][0 if side == "source" else 1]
        if cmds.objExists(node):
            cmds.select(node, replace=True)
            cmds.text(self.status, edit=True, label="已选择{0}骨骼：{1}".format(
                "源" if side == "source" else "目标", self._display_node_name(node)))

    def save_mapping_preset(self):
        result = cmds.fileDialog2(fileMode=0, dialogStyle=2, caption="保存映射预设",
                                  fileFilter="JSON 文件 (*.json)")
        if not result:
            return
        path = result[0]
        if not path.lower().endswith(".json"):
            path += ".json"
        mappings = []
        for row in self.rows:
            source = self._field_value(row["source"])
            target = self._field_value(row["target"])
            relative = self._field_value(row["relative"])
            if source and target:
                mappings.append({"source": source, "target": target, "relative": relative})
        data = {"format": "WRetargetToolPreset", "version": 1,
                "name_rules": cmds.textField(self.name_rules_field, query=True, text=True),
                "mappings": mappings}
        try:
            with io.open(path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
            cmds.text(self.status, edit=True, label="已保存 {0} 组映射预设。".format(len(mappings)))
        except Exception as error:
            cmds.warning("保存映射预设失败：{0}".format(error))

    def load_mapping_preset(self):
        result = cmds.fileDialog2(fileMode=1, dialogStyle=2, caption="载入映射预设",
                                  fileFilter="JSON 文件 (*.json)")
        if not result:
            return
        try:
            with io.open(result[0], "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if data.get("format") != "WRetargetToolPreset":
                raise RuntimeError("这不是 W Retarget Tool 的映射预设文件。")
            mappings = data.get("mappings", [])
            if not isinstance(mappings, list):
                raise RuntimeError("映射预设格式无效。")
            self._clear_rows()
            for mapping in mappings:
                row = self._first_empty_row()
                source = mapping.get("source", "")
                target = mapping.get("target", "")
                relative = mapping.get("relative", "")
                cmds.textField(row["source"], edit=True, text=self._display_node_name(source), annotation=source)
                cmds.textField(row["target"], edit=True, text=self._display_node_name(target), annotation=target)
                cmds.textField(row["relative"], edit=True, text=self._display_node_name(relative) if relative else "", annotation=relative)
            cmds.textField(self.name_rules_field, edit=True, text=data.get("name_rules", ""))
            cmds.text(self.status, edit=True, label="已载入 {0} 组映射预设。".format(len(mappings)))
        except Exception as error:
            cmds.warning("载入映射预设失败：{0}".format(error))

    def show_help(self):
        if cmds.window(HELP_WINDOW_NAME, exists=True):
            cmds.deleteUI(HELP_WINDOW_NAME)
        window = cmds.window(HELP_WINDOW_NAME, title="W 动画重定向工具 - 使用说明",
                             sizeable=True, widthHeight=(680, 520))
        cmds.columnLayout(adjustableColumn=True, rowSpacing=6)
        help_text = u"""W 动画重定向工具：使用说明

一、基础重定向
1. 设置开始帧和结束帧。源对象与目标对象应在开始帧处于相近的初始姿势。
2. 逐条填写“源对象”和“目标对象”，或使用下方的快速配对功能。
3. 点击“目标匹配源初始姿势”，让目标旋转与源对象视觉姿势一致。
4. 点击“全部重定向”。默认逐帧烘焙；取消“逐帧烘焙”后仅处理源对象有关键帧的时间点。

二、相对参考对象
留空时，源对象的运动相对其父级计算。层级结构不一致、或希望手相对胸部/脚相对骨盆计算时，可选择一个相对参考对象。

三、快速骨骼配对
1. 在 Outliner 中选择源骨架根节点，点击“设置源根”。
2. 选择目标骨架根节点，点击“设置目标根”。
3. 如名称不同，填写“名称替换规则”，格式为：旧名称=新名称;旧名称=新名称。
   示例：mixamorig:=;Left=L_;Right=R_;Hips=pelvis
4. 点击“生成候选”，检查候选列表后选择应用。

四、相似名称匹配
工具会在未匹配骨骼中比较名称相似度，并只给出“左右侧一致且互为最佳”的候选。相似度阈值默认 72%；提高阈值更安全，降低阈值候选更多但需要更仔细确认。
相似名称候选不会自动写入映射，必须点击“应用选中候选”或“应用全部候选”。

五、映射预设
完成一次人工确认后，点击“保存映射预设 JSON”。下次加载同一套角色/命名结构时，可用“载入映射预设 JSON”快速恢复。

六、注意事项
- 目标的锁定通道或已有非动画输入连接会被跳过。
- 视觉姿势匹配默认只对齐旋转，以保留不同角色的比例；“同步映射根节点的位置”通常仅用于角色根节点。
- 每次“全部重定向”和“目标匹配源初始姿势”都可使用 Maya Undo 撤销。
"""
        cmds.scrollField(text=help_text, editable=False, wordWrap=True, height=430)
        cmds.button(label="关闭", command=lambda *_: cmds.deleteUI(window))
        cmds.showWindow(window)

    def _read_mappings(self):
        mappings = []
        errors = []
        for index, row in enumerate(self.rows, 1):
            source = self._field_value(row["source"])
            target = self._field_value(row["target"])
            relative = self._field_value(row["relative"])
            if not source and not target:
                continue
            if not source or not target:
                errors.append("映射 {0}：必须同时填写源对象和目标对象。".format(index))
                continue
            if source == target:
                errors.append("映射 {0}：源对象和目标对象不能是同一个节点。".format(index))
                continue
            if not cmds.objExists(source):
                errors.append("映射 {0}：源对象不存在：{1}".format(index, source))
                continue
            if not cmds.objExists(target):
                errors.append("映射 {0}：目标对象不存在：{1}".format(index, target))
                continue
            if relative and not cmds.objExists(relative):
                errors.append("映射 {0}：相对参考对象不存在：{1}".format(index, relative))
                continue
            mappings.append((source, target, relative))
        if errors:
            raise RuntimeError("\n".join(errors))
        if not mappings:
            raise RuntimeError("请至少填写一组完整的源对象和目标对象映射。")
        return mappings

    @staticmethod
    def _keyable_target_attributes(target):
        result = []
        for attribute in ATTRIBUTES:
            plug = target + "." + attribute
            if not cmds.objExists(plug):
                continue
            if cmds.getAttr(plug, lock=True):
                continue
            if cmds.listConnections(plug, source=True, destination=False):
                continue
            result.append(attribute)
        return result

    @staticmethod
    def _source_key_times(source, start_frame, end_frame):
        times = set()
        for attribute in ATTRIBUTES:
            values = cmds.keyframe(source + "." + attribute, query=True, timeChange=True) or []
            times.update(frame for frame in values if start_frame <= frame <= end_frame)
        return sorted(times)

    def _temporary_network(self, source, target, relative, bind_frame):
        """Create one temporary DG graph for a mapping and return its nodes."""
        # The offset must always be captured at the user-selected start frame,
        # not at whichever frame happened to be active when the button was hit.
        cmds.currentTime(bind_frame, edit=True)
        src_local = cmds.createNode("transform", name="wrRetarget_srcLocal#")
        src_parent = cmds.createNode("transform", name="wrRetarget_srcParent#")
        cmds.parent(src_local, src_parent)
        tgt_delta = cmds.createNode("transform", name="wrRetarget_tgtDelta#")
        tgt_parent = cmds.createNode("transform", name="wrRetarget_tgtParent#")
        cmds.parent(tgt_delta, tgt_parent)
        target_proxy = cmds.createNode("transform", name="wrRetarget_targetProxy#")

        # Capture source and target parent spaces at the start frame.
        cmds.delete(cmds.pointConstraint(source, src_parent))
        source_parent = relative or (cmds.listRelatives(source, parent=True, fullPath=True) or [None])[0]
        if source_parent:
            cmds.parentConstraint(source_parent, src_parent, maintainOffset=True)
        cmds.parentConstraint(source, src_local, maintainOffset=True)

        cmds.delete(cmds.pointConstraint(target, tgt_parent))
        cmds.delete(cmds.parentConstraint(target, target_proxy))
        target_parent = (cmds.listRelatives(target, parent=True, fullPath=True) or [None])[0]
        if target_parent:
            cmds.parent(tgt_parent, target_parent)
            cmds.parent(target_proxy, target_parent)
        cmds.parentConstraint(tgt_delta, target_proxy, maintainOffset=True)

        matrix = cmds.createNode("multMatrix", name="wrRetarget_matrix#")
        decompose = cmds.createNode("decomposeMatrix", name="wrRetarget_decompose#")
        cmds.connectAttr(src_local + ".worldMatrix[0]", matrix + ".matrixIn[0]", force=True)
        cmds.connectAttr(src_parent + ".worldInverseMatrix[0]", matrix + ".matrixIn[1]", force=True)
        cmds.connectAttr(matrix + ".matrixSum", decompose + ".inputMatrix", force=True)
        cmds.connectAttr(decompose + ".outputTranslate", tgt_delta + ".translate", force=True)
        cmds.connectAttr(decompose + ".outputRotate", tgt_delta + ".rotate", force=True)
        return [src_parent, tgt_parent, target_proxy, matrix, decompose]

    def _copy_mapping(self, source, target, relative, frames, bind_frame,
                      progress_offset, started_at):
        nodes = []
        writable = self._keyable_target_attributes(target)
        if not writable:
            cmds.warning("跳过 {0}：所有变换通道均被锁定或已有输入连接。".format(target))
            return 0
        try:
            nodes = self._temporary_network(source, target, relative, bind_frame)
            target_proxy = nodes[2]
            for local_index, frame in enumerate(frames, 1):
                if self.cancel_requested:
                    raise RuntimeError("用户已取消重定向。")
                cmds.currentTime(frame, edit=True)
                for attribute in writable:
                    cmds.setAttr(target + "." + attribute, cmds.getAttr(target_proxy + "." + attribute))
                    cmds.setKeyframe(target, attribute=attribute, time=frame)
                completed = progress_offset + local_index
                cmds.progressBar(self.progress, edit=True, progress=completed)
                elapsed = max(time.time() - started_at, 0.001)
                remaining = (elapsed / completed) * (cmds.progressBar(self.progress, query=True, maxValue=True) - completed)
                total = cmds.progressBar(self.progress, query=True, maxValue=True)
                cmds.text(self.status, edit=True,
                          label="正在重定向：{0}/{1} 帧 | 预计剩余 {2:.1f} 秒".format(
                              completed, int(total), max(remaining, 0.0)))
                cmds.refresh(force=False)
            return len(frames)
        finally:
            existing = [node for node in nodes if cmds.objExists(node)]
            if existing:
                cmds.delete(existing)

    def _request_cancel(self):
        self.cancel_requested = True
        cmds.text(self.status, edit=True, label="已请求取消；将在当前帧处理完成后清理临时节点...")

    @staticmethod
    def _dag_depth(node):
        """Order parent mappings before children when matching a full pose."""
        return len((cmds.ls(node, long=True) or [node])[0].split("|"))

    def match_initial_pose(self):
        """Match target rotations to source rotations at the chosen start frame.

        This is intentionally a visual-pose helper: translations stay on the
        target so characters with different proportions do not collapse onto
        the source.  Optionally, only mapping roots receive source translation.
        """
        try:
            mappings = self._read_mappings()
            bind_frame = cmds.intFieldGrp(self.start_field, query=True, value1=True)
        except RuntimeError as error:
            cmds.warning(str(error))
            cmds.text(self.status, edit=True, label=str(error))
            return

        copy_root_translation = cmds.checkBox(self.match_root_translation_field,
                                               query=True, value=True)
        write_keys = cmds.checkBox(self.key_bind_pose_field, query=True, value=True)
        original_time = cmds.currentTime(query=True)
        original_selection = cmds.ls(selection=True, long=True) or []
        target_nodes = set(target for _, target, _ in mappings)
        roots = set()
        for _, target, _ in mappings:
            parent = (cmds.listRelatives(target, parent=True, fullPath=True) or [None])[0]
            if parent not in target_nodes:
                roots.add(target)

        completed = 0
        failures = []
        cmds.undoInfo(openChunk=True, chunkName="W Retarget Match Initial Pose")
        cmds.refresh(suspend=True)
        try:
            cmds.currentTime(bind_frame, edit=True)
            # A parent must be oriented first so child matching sees its final
            # target parent space, rather than yesterday's pose.
            for source, target, _ in sorted(mappings, key=lambda item: self._dag_depth(item[1])):
                try:
                    orient_constraint = cmds.orientConstraint(source, target, maintainOffset=False)
                    cmds.delete(orient_constraint)
                    if copy_root_translation and target in roots:
                        point_constraint = cmds.pointConstraint(source, target, maintainOffset=False)
                        cmds.delete(point_constraint)
                    if write_keys:
                        attributes = self._keyable_target_attributes(target)
                        for attribute in attributes:
                            cmds.setKeyframe(target, attribute=attribute, time=bind_frame)
                    completed += 1
                except Exception as error:
                    failures.append("{0} → {1}: {2}".format(source, target, error))
        finally:
            cmds.refresh(suspend=False)
            cmds.currentTime(original_time, edit=True)
            cmds.select(original_selection, replace=True) if original_selection else cmds.select(clear=True)
            cmds.undoInfo(closeChunk=True)

        if failures:
            cmds.warning("以下映射无法匹配初始姿势：\n" + "\n".join(failures))
            cmds.text(self.status, edit=True,
                      label="已匹配 {0} 组；{1} 组失败，请查看 Script Editor。".format(completed, len(failures)))
        else:
            cmds.text(self.status, edit=True,
                      label="已在第 {0} 帧将 {1} 个目标对象匹配到源对象初始姿势。".format(bind_frame, completed))

    def retarget_all(self):
        try:
            mappings = self._read_mappings()
            start_frame = cmds.intFieldGrp(self.start_field, query=True, value1=True)
            end_frame = cmds.intFieldGrp(self.end_field, query=True, value1=True)
            if end_frame < start_frame:
                raise RuntimeError("结束帧必须大于或等于开始帧。")
            key_all = cmds.checkBox(self.key_all_field, query=True, value=True)
            frame_sets = []
            for source, target, relative in mappings:
                frames = list(range(start_frame, end_frame + 1)) if key_all else self._source_key_times(source, start_frame, end_frame)
                if frames:
                    frame_sets.append((source, target, relative, frames))
                else:
                    cmds.warning("跳过 {0}：指定范围内没有源对象关键帧。".format(source))
            if not frame_sets:
                raise RuntimeError("没有可用于重定向的帧。")
        except RuntimeError as error:
            cmds.warning(str(error))
            cmds.text(self.status, edit=True, label=str(error))
            return

        original_time = cmds.currentTime(query=True)
        original_selection = cmds.ls(selection=True, long=True) or []
        total = sum(len(item[3]) for item in frame_sets)
        self.cancel_requested = False
        cmds.progressBar(self.progress, edit=True, minValue=0, maxValue=total, progress=0)
        cmds.undoInfo(openChunk=True, chunkName="W Retarget")
        cmds.refresh(suspend=True)
        completed = 0
        started_at = time.time()
        try:
            for source, target, relative, frames in frame_sets:
                completed += self._copy_mapping(source, target, relative, frames,
                                                start_frame, completed, started_at)
            cmds.text(self.status, edit=True, label="已完成 {0} 组映射，耗时 {1:.2f} 秒。".format(len(frame_sets), time.time() - started_at))
        except RuntimeError as error:
            cmds.warning(str(error))
            cmds.text(self.status, edit=True, label=str(error))
        except Exception as error:
            cmds.warning("重定向失败：{0}".format(error))
            cmds.text(self.status, edit=True, label="失败：{0}".format(error))
        finally:
            cmds.refresh(suspend=False)
            cmds.currentTime(original_time, edit=True)
            cmds.select(original_selection, replace=True) if original_selection else cmds.select(clear=True)
            cmds.undoInfo(closeChunk=True)

    def _choose_export_folder(self):
        result = cmds.fileDialog2(fileMode=3, dialogStyle=2, caption="选择 FBX 输出文件夹")
        if result:
            cmds.textField(self.export_path_field, edit=True, text=result[0])

    def export_targets(self):
        try:
            targets = []
            for _, target, _ in self._read_mappings():
                if target not in targets:
                    targets.append(target)
            output_folder = cmds.textField(self.export_path_field, query=True, text=True).strip()
            if not output_folder or not os.path.isdir(output_folder):
                raise RuntimeError("请选择一个已存在的 FBX 输出文件夹。")
            if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
                cmds.loadPlugin("fbxmaya", quiet=True)
        except Exception as error:
            cmds.warning("无法导出：{0}".format(error))
            return

        original_selection = cmds.ls(selection=True, long=True) or []
        try:
            mel.eval("FBXResetExport;")
            for target in targets:
                safe_name = target.split("|")[-1].replace(":", "_")
                path = os.path.join(output_folder, safe_name + ".fbx").replace("\\", "/")
                cmds.select(target, replace=True)
                cmds.file(path, force=True, options="v=0;", type="FBX export", preserveReferences=True, exportSelected=True)
            cmds.text(self.status, edit=True, label="已导出 {0} 个目标变换节点。".format(len(targets)))
        except Exception as error:
            cmds.warning("FBX 导出失败：{0}".format(error))
        finally:
            cmds.select(original_selection, replace=True) if original_selection else cmds.select(clear=True)


def show():
    return RetargetTool()


show()
