# Maya `cmds` UI 组件参数参考

本文档整理 `WretargetToolOptimized.py` 中使用到的 Maya Python UI 组件。

> 说明：Maya 不同版本支持的参数可能略有差异。实际使用时，以当前 Maya 版本的 `cmds` 文档和 Script Editor 报错信息为准。

## 1. 通用规则

### 创建控件

```python
control = cmds.button(
    label="开始",
    width=120,
    height=28
)
```

Maya 会返回控件名称，例如：

```python
'button1'
```

### 修改控件

```python
cmds.button(
    control,
    edit=True,
    label="处理中...",
    enable=False
)
```

### 查询控件

```python
text = cmds.textField(
    field,
    query=True,
    text=True
)
```

### 常见通用参数

| 参数 | 作用 | 示例 |
|---|---|---|
| `parent` | 指定父布局 | `parent=layout` |
| `width` | 宽度，单位通常为像素 | `width=120` |
| `height` | 高度 | `height=28` |
| `visible` | 是否显示 | `visible=True` |
| `enable` | 是否可操作 | `enable=False` |
| `annotation` | 鼠标悬停提示 | `annotation="说明文字"` |
| `backgroundColor` | 背景颜色，RGB 范围 0～1 | `(0.2, 0.4, 0.6)` |
| `manage` | 是否由 Maya 管理布局空间 | `manage=False` |
| `statusBarMessage` | 状态栏提示 | `statusBarMessage="点击执行"` |

---

## 2. `cmds.button()` 按钮

### 基本写法

```python
cmds.button(
    label="新增映射行",
    width=120,
    height=28,
    command=lambda *_: self._add_row()
)
```

### 常用参数

| 参数 | 说明 |
|---|---|
| `label` | 按钮显示文字 |
| `command` | 点击按钮时执行的函数 |
| `width` | 按钮宽度 |
| `height` | 按钮高度 |
| `backgroundColor` | 背景颜色 |
| `annotation` | 悬停提示 |
| `enable` | 是否启用 |
| `visible` | 是否显示 |
| `align` | 文字对齐：`left`、`center`、`right` |
| `actOnPress` | 按下鼠标时立即执行 |
| `repeating` | 按住按钮时重复执行 |
| `image` | 使用图标 |

### 回调函数

Maya 通常会向回调函数传入一个参数，因此常见写法是：

```python
command=lambda *_: self.retarget_all()
```

也可以使用普通函数：

```python
def on_click(*args):
    print("按钮被点击")

cmds.button(label="测试", command=on_click)
```

### 修改和查询

```python
cmds.button(button_name, edit=True, label="完成", enable=True)

label = cmds.button(button_name, query=True, label=True)
```

---

## 3. `cmds.text()` 文本标签

```python
cmds.text(
    label="帧范围",
    width=70,
    height=24,
    align="right"
)
```

### 常用参数

| 参数 | 说明 |
|---|---|
| `label` | 显示文字 |
| `align` | 对齐方式 |
| `width` | 宽度 |
| `height` | 高度 |
| `font` | 字体，如 `plainLabelFont`、`boldLabelFont` |
| `wordWrap` | 是否自动换行 |
| `backgroundColor` | 背景颜色 |
| `enable` | 是否启用显示 |
| `annotation` | 悬停说明 |
| `recomputeSize` | 是否根据文字重新计算尺寸 |

```python
title = cmds.text(
    label="W RETARGET TOOL",
    font="boldLabelFont",
    height=30,
    align="left"
)

cmds.text(title, edit=True, label="处理中...")
```

---

## 4. `cmds.textField()` 单行文本输入框

```python
field = cmds.textField(
    width=240,
    height=24,
    placeholderText="请输入节点名称"
)
```

### 常用参数

| 参数 | 说明 |
|---|---|
| `text` | 初始文本 |
| `placeholderText` | 占位提示文字 |
| `width` | 宽度 |
| `height` | 高度 |
| `editable` | 是否允许编辑 |
| `enable` | 是否启用 |
| `annotation` | 悬停提示 |
| `changeCommand` | 内容改变时回调 |
| `enterCommand` | 按 Enter 时回调 |
| `receiveFocusCommand` | 获得焦点时回调 |
| `失去焦点回调` | 具体参数因 Maya 版本而异 |

### 读取、修改和清空

```python
value = cmds.textField(field, query=True, text=True)

cmds.textField(field, edit=True, text="pCube1")

cmds.textField(field, edit=True, text="", annotation="")
```

---

## 5. `cmds.intField()` 整数输入框

```python
field = cmds.intField(
    value=72,
    minValue=0,
    maxValue=100,
    step=1,
    width=80
)
```

### 常用参数

| 参数 | 说明 |
|---|---|
| `value` | 初始整数值 |
| `minValue` | 最小值 |
| `maxValue` | 最大值 |
| `step` | 每次增减的步长 |
| `width` | 宽度 |
| `height` | 高度 |
| `changeCommand` | 数值变化时回调 |
| `enable` | 是否启用 |

```python
value = cmds.intField(field, query=True, value=True)
cmds.intField(field, edit=True, value=80)
```

---

## 6. `cmds.intFieldGrp()` 带标签的整数输入框

```python
field = cmds.intFieldGrp(
    label="开始帧",
    numberOfFields=1,
    value1=0,
    minValue1=0,
    columnWidth2=(60, 100)
)
```

### 关键参数

| 参数 | 说明 |
|---|---|
| `label` | 标签文字 |
| `numberOfFields` | 输入框数量，通常为 1～4 |
| `value1`～`value4` | 各输入框初始值 |
| `minValue1`～`minValue4` | 各输入框最小值 |
| `maxValue1`～`maxValue4` | 各输入框最大值 |
| `columnWidth2` | 标签列宽度、输入框列宽度 |
| `columnWidth3` | 两个输入框时使用：标签、输入框1、输入框2 |
| `changeCommand` | 数值变化回调 |

```python
start = cmds.intFieldGrp(field, query=True, value1=True)
cmds.intFieldGrp(field, edit=True, value1=10)
```

---

## 7. `cmds.floatField()` 浮点数输入框

```python
field = cmds.floatField(
    value=0.0,
    minValue=-180.0,
    maxValue=180.0,
    precision=3,
    width=90
)
```

常用参数与 `intField()` 类似，区别是支持小数：

| 参数 | 说明 |
|---|---|
| `value` | 浮点数初始值 |
| `precision` | 小数位数 |
| `minValue` | 最小值 |
| `maxValue` | 最大值 |
| `step` | 步长 |

---

## 8. `cmds.checkBox()` 复选框

```python
check = cmds.checkBox(
    label="逐帧烘焙",
    value=True,
    width=100,
    height=24,
    annotation="处理范围内的每一帧"
)
```

### 常用参数

| 参数 | 说明 |
|---|---|
| `label` | 显示文字 |
| `value` | 是否默认勾选 |
| `width` | 宽度 |
| `height` | 高度 |
| `align` | 对齐方式 |
| `changeCommand` | 勾选状态变化回调 |
| `enable` | 是否启用 |
| `visible` | 是否显示 |
| `annotation` | 悬停提示 |

```python
enabled = cmds.checkBox(check, query=True, value=True)
cmds.checkBox(check, edit=True, value=False)
```

---

## 9. `cmds.frameLayout()` 分组框

```python
frame = cmds.frameLayout(
    label="动画范围与烘焙选项",
    collapsable=True,
    collapse=False,
    marginWidth=5,
    marginHeight=3,
    backgroundColor=(0.18, 0.22, 0.28)
)
```

### 常用参数

| 参数 | 说明 |
|---|---|
| `label` | 分组标题 |
| `collapsable` | 是否允许折叠 |
| `collapse` | 初始是否折叠 |
| `marginWidth` | 内容左右边距 |
| `marginHeight` | 内容上下边距 |
| `borderVisible` | 是否显示边框 |
| `labelAlign` | 标题对齐 |
| `backgroundColor` | 背景颜色 |
| `collapseCommand` | 折叠时回调 |
| `expandCommand` | 展开时回调 |

```python
cmds.frameLayout(frame, edit=True, collapse=True)
is_collapsed = cmds.frameLayout(frame, query=True, collapse=True)
```

---

## 10. `cmds.rowLayout()` 横向布局

```python
layout = cmds.rowLayout(
    numberOfColumns=3,
    columnWidth3=(80, 220, 100),
    adjustableColumn=2,
    columnAttach=[
        (1, "both", 2),
        (2, "both", 2),
        (3, "both", 2)
    ]
)
```

### 关键参数

| 参数 | 说明 |
|---|---|
| `numberOfColumns` | 列数 |
| `columnWidth` | 每列宽度，通用列表格式 |
| `columnWidth2` | 两列宽度 |
| `columnWidth3` | 三列宽度 |
| `columnWidth4` | 四列宽度 |
| `adjustableColumn` | 可伸缩列编号，只能指定一个 |
| `columnAttach` | 每列对齐方式和间距 |
| `columnAlign` | 每列内容对齐 |
| `rowAttach` | 行垂直方向对齐 |
| `parent` | 父布局 |

`columnWidth2=(35, 75)` 表示两列宽度分别为 35 和 75 像素。

`columnAttach=[(1, "both", 2)]` 表示第 1 列左右贴合，边距为 2 像素。

> 注意：一个 `rowLayout` 通常只能设置一个 `adjustableColumn`。如果需要多个输入框同时自适应，考虑 `formLayout` 或拆分多个布局。

---

## 11. `cmds.columnLayout()` 纵向布局

```python
layout = cmds.columnLayout(
    adjustableColumn=True,
    rowSpacing=4
)
```

| 参数 | 说明 |
|---|---|
| `adjustableColumn` | 是否让子控件填满可用宽度 |
| `rowSpacing` | 子控件之间的垂直间距 |
| `columnAlign` | 子控件对齐 |
| `columnWidth` | 默认列宽 |
| `parent` | 父布局 |

---

## 12. `cmds.formLayout()` 表单布局

适合需要多个控件同时自适应的复杂表格。

```python
layout = cmds.formLayout()
label = cmds.text(parent=layout, label="源")
field = cmds.textField(parent=layout)
button = cmds.button(parent=layout, label="选择")

cmds.formLayout(
    layout,
    edit=True,
    attachForm=[
        (label, "left", 4),
        (button, "right", 4)
    ],
    attachControl=[
        (field, "left", 4, label),
        (field, "right", 4, button)
    ],
    attachPosition=[
        (label, "left", 0, 0),
        (field, "left", 0, 15),
        (button, "left", 0, 85)
    ]
)
```

常用约束参数：

| 参数 | 说明 |
|---|---|
| `attachForm` | 控件与布局边缘绑定 |
| `attachControl` | 控件与其他控件绑定 |
| `attachPosition` | 按百分比位置绑定 |
| `attachNone` | 取消某方向约束 |
| `attachOppositeForm` | 绑定到布局相反边缘 |

---

## 13. `cmds.scrollLayout()` 滚动布局

```python
scroll = cmds.scrollLayout(
    childResizable=True,
    horizontalScrollBarThickness=12,
    verticalScrollBarThickness=14
)
```

| 参数 | 说明 |
|---|---|
| `childResizable` | 子布局是否跟随滚动区域宽度 |
| `horizontalScrollBarThickness` | 水平滚动条厚度 |
| `verticalScrollBarThickness` | 垂直滚动条厚度 |
| `minChildWidth` | 子内容最小宽度 |
| `minChildHeight` | 子内容最小高度 |

---

## 14. `cmds.textScrollList()` 文本列表

```python
items = cmds.textScrollList(
    numberOfRows=6,
    height=120,
    allowMultiSelection=True,
    selectCommand=lambda *_: self.select_candidate_bone("source")
)
```

| 参数 | 说明 |
|---|---|
| `append` | 添加一条或多条文本 |
| `removeAll` | 清空列表 |
| `numberOfRows` | 默认显示行数 |
| `height` | 列表高度 |
| `allowMultiSelection` | 是否允许多选 |
| `selectCommand` | 选择变化时回调 |
| `selectIndexedItem` | 查询或设置选中行编号 |
| `removeIndexedItem` | 删除指定行 |

```python
cmds.textScrollList(items, edit=True, append="左臂 -> LeftArm")
selected = cmds.textScrollList(items, query=True, selectIndexedItem=True) or []
cmds.textScrollList(items, edit=True, removeAll=True)
```

---

## 15. `cmds.progressBar()` 进度条

```python
progress = cmds.progressBar(
    minValue=0,
    maxValue=100,
    progress=0
)
```

```python
cmds.progressBar(progress, edit=True, progress=50)
value = cmds.progressBar(progress, query=True, progress=True)
maximum = cmds.progressBar(progress, query=True, maxValue=True)
```

常用参数：

| 参数 | 说明 |
|---|---|
| `minValue` | 最小值 |
| `maxValue` | 最大值 |
| `progress` | 当前进度 |
| `isInterruptable` | 是否允许中断 |
| `status` | 进度文字，部分版本支持 |
| `width` | 宽度 |
| `height` | 高度 |

---

## 16. `cmds.separator()` 分隔线

```python
cmds.separator(
    style="in",
    height=8
)
```

常见参数：

| 参数 | 说明 |
|---|---|
| `style` | `in`、`out`、`etched`、`none` |
| `height` | 分隔线高度 |
| `width` | 分隔线宽度 |
| `visible` | 是否显示 |

---

## 17. `cmds.window()` 窗口

```python
window = cmds.window(
    title="动画重定向工具",
    sizeable=True,
    widthHeight=(980, 650),
    minimizeButton=True,
    maximizeButton=False
)
```

| 参数 | 说明 |
|---|---|
| `title` | 窗口标题 |
| `sizeable` | 是否允许调整窗口大小 |
| `widthHeight` | 初始宽度和高度 |
| `minimizeButton` | 是否显示最小化按钮 |
| `maximizeButton` | 是否显示最大化按钮 |
| `resizeToFitChildren` | 是否根据子控件自动调整 |
| `retain` | 关闭后是否保留窗口 |

显示窗口：

```python
cmds.showWindow(window)
```

删除窗口：

```python
if cmds.window("MyWindow", exists=True):
    cmds.deleteUI("MyWindow")
```

---

## 18. 布局切换：`setParent()`

```python
frame = cmds.frameLayout(label="设置")
cmds.columnLayout(adjustableColumn=True)
cmds.text(label="内容")

cmds.setParent("..")  # 返回 frameLayout
cmds.setParent("..")  # 返回上一级布局
```

也可以使用明确的父布局：

```python
layout = cmds.columnLayout()
cmds.button(parent=layout, label="按钮")
```

大型 UI 更推荐明确传入 `parent=`，可以减少 `setParent("..")` 层级错误。

---

## 19. 颜色设置

Maya 使用 0～1 范围的 RGB 数值：

```python
backgroundColor=(0.2, 0.4, 0.8)
```

常用颜色示例：

```python
dark_gray = (0.18, 0.18, 0.18)
blue = (0.25, 0.45, 0.70)
green = (0.30, 0.68, 0.32)
orange = (0.78, 0.40, 0.20)
```

如果手头是 0～255 的 RGB，需要转换：

```python
rgb_255 = (64, 128, 200)
rgb_maya = tuple(value / 255.0 for value in rgb_255)
```

---

## 20. 常见注意事项

1. `rowLayout` 的 `adjustableColumn` 通常只能指定一个列。
2. 父布局的列宽可能覆盖子控件的 `width` 设置。
3. 修改已经打开的窗口不会自动更新，通常需要删除旧窗口后重新执行脚本。
4. `command` 回调建议使用 `lambda *_:`，以兼容 Maya 传入的参数。
5. 中文文字显示异常时，检查脚本文件编码是否为 UTF-8。
6. 动态删除控件前，建议先检查：

```python
if cmds.control(control_name, exists=True):
    cmds.deleteUI(control_name)
```

