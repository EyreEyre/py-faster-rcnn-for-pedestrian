---
typora-copy-images-to: ..\img\Experiment\py-faster-rcnn-caltech-pedestrian
---

## 1. Baseline

- 各类论文中faster rcnn在caltech上的结果为20.98%
- 按照README.md跑通代码，发现AP很低，但是通过转换为caltech的格式后评估结果MR=26.84%
- 增加训练数据，caltech_train_10x，得到的AP有提升但还是很低，但是MR=21.21%，基本接近其他论文中的结果。因此分析可能是AP计算时考虑了所有的GT


## 2. 复现CityPerson的结果

在论文中提到了对Faster R-CNN的五点修改

- **M1** 修改anchor尺寸
- **M2** 图像升采样
- **M3** 减小feature stride
- **M4** 处理handling
- **M5** 使用ADAM

下面是对每个修改进行复现

### M1 修改anchor尺寸

论文中没有给出anchor的分布，因此我们考虑采用RPN+BF的anchor设置，修改后MR应下降2-3点

- 修改anchor为RPN+BF的设置
  -  [commit](https://github.com/xzhewei/py-faster-rcnn-for-pedestrian/commit/e2fd3ec00951c0a4a2c6cb8a716c9617ee66757c)
  - 从训练过程中发现，Fast训练的fg样本明显减少，之前fg:bg=0.11左右，目前是0.048左右。fg减少带来的样本不平衡可能导致训练受背景的影响增加，之后可考虑采用动态batchsize，看是否可行，即将正负样本比例固定在一个合适的值。MR=54.79%，明显变差。可能是由于第二阶段的样本不平衡导致。
- 修改classes的类别，仅有background和person
  - [commit](https://github.com/xzhewei/py-faster-rcnn-for-pedestrian/commit/e2fd3ec00951c0a4a2c6cb8a716c9617ee66757c)
  - pyfaster-10x-anchor-E01，MR=60.08%。

