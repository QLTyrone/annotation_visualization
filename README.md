简体中文 | [English](doc/README_en.md)

本项目用于标注文档的可视化

在`visualizer.py`中, 提供了用于标注文档可视化的类. 该类用于对某一标注文档数据集进行可视化. 

## 使用方式
对一Visualizer对象, 可以首先通过set_XX_color更改对应颜色, 对于不同信息, 在初始化时已经预设好了颜色, 对实体的类型提供了30种预设的颜色, 当实体数目超过30时, 需要自行传入. 同时, 需要通过set_entity_types传入实体类型. 
在类的参数设置好后, 可以通过类中的visualize方法生成标注文档图片. 函数需要标注信息的json文件与输出路径. 其余参数为功能开关, 在下面详细介绍
- json是待解析的标注信息
- save_path是可视化后图片保存位置
- use_image是绘制左图的开关. 其为真, 则绘制左图右文, 并且需要提供image_path. 为假则只绘制文字. 
- image_path是图像的地址
- use_word是文+框显示级别的开关. 其为真, 则显示word级别. 为假则显示segment级别
- use_entity_type是实体类型显示的开关
- use_entity_text是实体内容文字显示的开关
- use_linking是实体链接显示的开关
- use_order是阅读顺序显示的开关