#! /bin/sh

#$ -l rt_G.large=1
#$ -l h_rt=6:00:00

#$ -m a
#$ -m b
#$ -m e
#$ -j y
#$ -cwd
source /etc/profile.d/modules.sh
module load gcc/9.3.0 python/3.8 cuda/11.3/11.3.1 cudnn/8.4/8.4.1

source /home/ace14496ms/anaconda3/etc/profile.d/conda.sh
conda activate open-mmlab

python /home/ace14496ms/mmdetection3d/tools/train_point_rcnn_2x8_kitti-3d-3classes.py \
	/home/ace14496ms/mmdetection3d/configs/point_rcnn/point_rcnn_2x8_kitti-3d-3classes.py

