# -----------------------------------------------------------
# 将骨骼（Joint）的绘制样式设为 "Bone"
# 适用于 Maya Script Editor 直接运行
# -----------------------------------------------------------
import maya.cmds as cmds

def set_joints_to_bone_draw_style(selection_only=False):
    """
    将关节的 drawStyle 设置为 Bone (0)
    :param selection_only: True = 仅处理选中的关节；False = 处理场景中所有关节
    """
    if selection_only:
        # 获取选中的关节（包括子层级）
        selected = cmds.ls(selection=True, long=True)
        if not selected:
            cmds.warning("请先选择至少一个关节。")
            return
        # 从选中对象中提取所有关节（包括子级）
        joints = []
        for node in selected:
            if cmds.nodeType(node) == "joint":
                joints.append(node)
            # 添加子级中的关节
            children_joints = cmds.listRelatives(node, allDescendents=True, type="joint", fullPath=True) or []
            joints.extend(children_joints)
        joints = list(set(joints))  # 去重
    else:
        # 获取场景中所有关节
        joints = cmds.ls(type="joint", long=True)

    if not joints:
        cmds.warning("场景中未找到任何关节。")
        return

    modified_count = 0
    for jnt in joints:
        if not cmds.objExists(jnt):
            continue
        try:
            # 检查属性是否存在且可写
            if cmds.attributeQuery("drawStyle", node=jnt, exists=True):
                if not cmds.getAttr(f"{jnt}.drawStyle", lock=True):
                    cmds.setAttr(f"{jnt}.drawStyle", 0)  # 0 = Bone
                    modified_count += 1
                else:
                    cmds.warning(f"跳过锁定的关节: {jnt}")
        except Exception as e:
            cmds.warning(f"无法设置 {jnt} 的 drawStyle: {e}")

    cmds.inViewMessage(
        amg=f'<hl>完成！</hl><br>{modified_count} 个关节已设为 Bone 样式',
        pos='midCenter',
        fade=True
    )
    print(f"[INFO] 已将 {modified_count} 个关节的绘制样式设为 'Bone'")

# ------------------ 执行 ------------------
# 修改下面的参数来控制行为：
if __name__ == "__main__":
    # True = 仅处理选中的关节及其子级
    # False = 处理整个场景的所有关节
    set_joints_to_bone_draw_style(selection_only=True)