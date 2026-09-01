# -*- coding: utf-8 -*-
"""W Retarget Tool Optimized.

Run this file inside Maya's Script Editor.  It is deliberately standalone and
does not modify either of the original tools.
"""
from __future__ import print_function

import os
import time

import maya.cmds as cmds
import maya.mel as mel


WINDOW_NAME = "WRetargetToolOptimized"
ATTRIBUTES = ("tx", "ty", "tz", "rx", "ry", "rz")


class RetargetTool(object):
    """Matrix based, non-destructive animation retargeting UI."""

    def __init__(self):
        self.rows = []
        self.cancel_requested = False
        self.progress = None
        self.status = None
        self.start_field = None
        self.end_field = None
        self.key_all_field = None
        self.export_path_field = None
        self._build_ui()

    def _build_ui(self):
        if cmds.window(WINDOW_NAME, exists=True):
            cmds.deleteUI(WINDOW_NAME)

        window = cmds.window(WINDOW_NAME, title="W 动画重定向工具 - 优化版",
                             sizeable=True, widthHeight=(840, 430))
        cmds.columnLayout(adjustableColumn=True, rowSpacing=6)
        cmds.text(label="矩阵动画重定向：源对象与目标对象应在起始帧保持相同的绑定／初始姿势",
                  align="left")

        cmds.rowLayout(numberOfColumns=5, adjustableColumn=5,
                       columnWidth5=(120, 150, 150, 160, 200))
        cmds.text(label="动画帧范围")
        self.start_field = cmds.intFieldGrp(label="开始", numberOfFields=1, value1=0,
                                             columnWidth2=(45, 75))
        self.end_field = cmds.intFieldGrp(label="结束", numberOfFields=1, value1=20,
                                           columnWidth2=(35, 75))
        self.key_all_field = cmds.checkBox(label="逐帧烘焙", value=True)
        cmds.button(label="添加映射", command=lambda *_: self._add_row())
        cmds.setParent("..")

        cmds.separator(style="in")
        self.mapping_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        for _ in range(4):
            self._add_row()
        cmds.setParent("..")

        cmds.rowLayout(numberOfColumns=4, adjustableColumn=1,
                       columnWidth4=(220, 180, 180, 180))
        cmds.button(label="移除空映射", command=lambda *_: self._remove_empty_rows())
        cmds.button(label="全部重定向", backgroundColor=(0.35, 0.75, 0.35),
                    command=lambda *_: self.retarget_all())
        cmds.button(label="取消", backgroundColor=(0.8, 0.45, 0.25),
                    command=lambda *_: self._request_cancel())
        cmds.button(label="清空映射", command=lambda *_: self._clear_rows())
        cmds.setParent("..")

        self.progress = cmds.progressBar(maxValue=1, width=500)
        self.status = cmds.text(label="就绪", align="left")
        cmds.separator(style="in")

        scene_path = cmds.file(query=True, sceneName=True) or ""
        default_path = os.path.dirname(scene_path) if scene_path else ""
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnWidth3=(120, 570, 110))
        cmds.text(label="FBX 输出文件夹")
        self.export_path_field = cmds.textField(text=default_path)
        cmds.button(label="选择...", command=lambda *_: self._choose_export_folder())
        cmds.setParent("..")
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(230, 200))
        cmds.button(label="将目标节点导出为 FBX", command=lambda *_: self.export_targets())
        cmds.text(label="仅导出映射中填写的目标节点", align="left")
        cmds.setParent("..")

        cmds.showWindow(window)

    def _add_row(self):
        # ``columnWidth7`` is unsupported by several Maya releases.  The
        # generic columnWidth flag works across those releases.
        row = cmds.rowLayout(parent=self.mapping_layout, numberOfColumns=8,
                             adjustableColumn=2,
                             columnWidth=[(1, 75), (2, 220), (3, 75),
                                          (4, 170), (5, 80), (6, 170),
                                          (7, 80), (8, 45)])
        cmds.text(label="源对象")
        source = cmds.textField()
        cmds.button(label="使用选择", command=lambda *_: self._set_selected(source))
        target = cmds.textField(placeholderText="目标对象")
        cmds.button(label="设置目标", command=lambda *_: self._set_selected(target))
        relative = cmds.textField(placeholderText="可选：相对参考对象")
        cmds.button(label="设置参考", command=lambda *_: self._set_selected(relative))
        remove = cmds.button(label="删除", command=lambda *_: self._delete_row(row))
        self.rows.append({"layout": row, "source": source, "target": target,
                          "relative": relative, "remove": remove})

    def _delete_row(self, layout):
        self.rows = [row for row in self.rows if row["layout"] != layout]
        if cmds.control(layout, exists=True):
            cmds.deleteUI(layout)

    def _set_selected(self, field):
        selection = cmds.ls(selection=True, long=True) or []
        if not selection:
            cmds.warning("请先选择一个变换节点。")
            return
        cmds.textField(field, edit=True, text=selection[0])

    def _clear_rows(self):
        for row in self.rows:
            for field in (row["source"], row["target"], row["relative"]):
                cmds.textField(field, edit=True, text="")

    def _remove_empty_rows(self):
        for row in list(self.rows):
            if not cmds.textField(row["source"], query=True, text=True).strip() and not cmds.textField(row["target"], query=True, text=True).strip():
                self._delete_row(row["layout"])
        if not self.rows:
            self._add_row()

    def _read_mappings(self):
        mappings = []
        errors = []
        for index, row in enumerate(self.rows, 1):
            source = cmds.textField(row["source"], query=True, text=True).strip()
            target = cmds.textField(row["target"], query=True, text=True).strip()
            relative = cmds.textField(row["relative"], query=True, text=True).strip()
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
                cmds.text(self.status, edit=True, label="正在重定向 {0} → {1} | 预计剩余 {2:.1f} 秒".format(source, target, max(remaining, 0.0)))
                cmds.refresh(force=False)
            return len(frames)
        finally:
            existing = [node for node in nodes if cmds.objExists(node)]
            if existing:
                cmds.delete(existing)

    def _request_cancel(self):
        self.cancel_requested = True
        cmds.text(self.status, edit=True, label="已请求取消；将在当前帧处理完成后清理临时节点...")

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
