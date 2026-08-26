import maya.cmds as cmds

def shift_keys_to_zero():
    # 获取选择对象，如果没有选择则获取所有关节
    sel = cmds.ls(sl=True, type='transform') or cmds.ls(type='joint')
    if not sel:
        cmds.warning("请先选择骨骼根节点或控制器")
        return
    
    processed_curves = set()  # 避免重复处理共享曲线
    
    for obj in sel:
        anim_curves = cmds.listConnections(obj, s=True, d=False, type='animCurve') or []
        valid_curves = [c for c in anim_curves if c not in processed_curves]
        
        if not valid_curves:
            continue
            
        min_time = float('inf')
        has_valid_key = False
        
        # 安全地查找最小时间
        for curve in valid_curves:
            try:
                keys = cmds.keyframe(curve, q=True, tc=True)
                # 关键修复：确保keys是非空列表且包含数字
                if keys and isinstance(keys, list) and len(keys) > 0:
                    current_min = min(float(k) for k in keys)
                    if current_min < min_time:
                        min_time = current_min
                    has_valid_key = True
            except Exception as e:
                cmds.warning(f"跳过曲线 {curve}: {e}")
                continue
        
        # 只有找到有效关键帧且不在0帧时才偏移
        if has_valid_key and min_time != float('inf') and abs(min_time) > 0.001:
            offset = -float(min_time)
            for curve in valid_curves:
                try:
                    cmds.keyframe(curve, edit=True, relative=True, timeChange=offset)
                except Exception as e:
                    cmds.warning(f"偏移失败 {curve}: {e}")
            
            print(f"{obj}: 偏移 {offset:.4f} 帧 (原始起始: {min_time:.4f})")
            processed_curves.update(valid_curves)
        else:
            print(f"{obj}: 无需偏移 (起始已在0或无关键帧)")

shift_keys_to_zero()