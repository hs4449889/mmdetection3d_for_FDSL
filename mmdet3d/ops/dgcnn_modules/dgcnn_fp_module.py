# Copyright (c) OpenMMLab. All rights reserved.
from mmcv.cnn import ConvModule
from mmcv.runner import BaseModule, force_fp32
from torch import nn as nn


class DGCNNFPModule(BaseModule):
    """Point feature propagation module used in DGCNN.

    Propagate the features from one set to another.

    Args:
        mlp_channels (list[int]): List of mlp channels.
        norm_cfg (dict, optional): Type of activation method.
            Defaults to dict(type='BN1d').
        act_cfg (dict, optional): Type of activation method.
            Defaults to dict(type='ReLU').
        init_cfg (dict, optional): Initialization config. Defaults to None.
    """

    def __init__(
        self,
        mlp_channels,
        norm_cfg=dict(type="BN1d"),
        act_cfg=dict(type="ReLU"),
        init_cfg=None,
    ):
        super().__init__(init_cfg=init_cfg)
        self.fp16_enabled = False
        self.mlps = nn.Sequential()
        for i in range(len(mlp_channels) - 1):
            self.mlps.add_module(
                f"layer{i}",
                ConvModule(
                    mlp_channels[i],
                    mlp_channels[i + 1],
                    kernel_size=(1,),
                    stride=(1,),
                    conv_cfg=dict(type="Conv1d"),
                    norm_cfg=norm_cfg,
                    act_cfg=act_cfg,
                ),
            )

    @force_fp32()
    def forward(self, points):
        """forward.

        Args:
            points (Tensor): (B, N, C) tensor of the input points.

        Returns:
            Tensor: (B, N, M) M = mlp[-1], tensor of the new points.
        """

        if points is not None:
            new_points = points.transpose(1, 2).contiguous()  # (B, C, N)
            new_points = self.mlps(new_points)
            new_points = new_points.transpose(1, 2).contiguous()
        else:
            new_points = points

        return new_points
