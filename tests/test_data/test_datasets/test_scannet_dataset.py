# Copyright (c) OpenMMLab. All rights reserved.
import copy

import numpy as np
import pytest
import torch

from mmdet3d.datasets import (
    ScanNetDataset,
    ScanNetInstanceSegDataset,
    ScanNetSegDataset,
)


def test_getitem():
    np.random.seed(0)
    root_path = "./tests/data/scannet/"
    ann_file = "./tests/data/scannet/scannet_infos.pkl"
    class_names = (
        "cabinet",
        "bed",
        "chair",
        "sofa",
        "table",
        "door",
        "window",
        "bookshelf",
        "picture",
        "counter",
        "desk",
        "curtain",
        "refrigerator",
        "showercurtrain",
        "toilet",
        "sink",
        "bathtub",
        "garbagebin",
    )
    pipelines = [
        dict(
            type="LoadPointsFromFile",
            coord_type="DEPTH",
            shift_height=True,
            load_dim=6,
            use_dim=[0, 1, 2],
        ),
        dict(
            type="LoadAnnotations3D",
            with_bbox_3d=True,
            with_label_3d=True,
            with_mask_3d=True,
            with_seg_3d=True,
        ),
        dict(type="GlobalAlignment", rotation_axis=2),
        dict(
            type="PointSegClassMapping",
            valid_cat_ids=(
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                14,
                16,
                24,
                28,
                33,
                34,
                36,
                39,
            ),
        ),
        dict(type="PointSample", num_points=5),
        dict(
            type="RandomFlip3D",
            sync_2d=False,
            flip_ratio_bev_horizontal=1.0,
            flip_ratio_bev_vertical=1.0,
        ),
        dict(
            type="GlobalRotScaleTrans",
            rot_range=[-0.087266, 0.087266],
            scale_ratio_range=[1.0, 1.0],
            shift_height=True,
        ),
        dict(type="DefaultFormatBundle3D", class_names=class_names),
        dict(
            type="Collect3D",
            keys=[
                "points",
                "gt_bboxes_3d",
                "gt_labels_3d",
                "pts_semantic_mask",
                "pts_instance_mask",
            ],
            meta_keys=["file_name", "sample_idx", "pcd_rotation"],
        ),
    ]

    scannet_dataset = ScanNetDataset(root_path, ann_file, pipelines)
    data = scannet_dataset[0]
    points = data["points"]._data
    gt_bboxes_3d = data["gt_bboxes_3d"]._data
    gt_labels = data["gt_labels_3d"]._data
    pts_semantic_mask = data["pts_semantic_mask"]._data
    pts_instance_mask = data["pts_instance_mask"]._data
    file_name = data["img_metas"]._data["file_name"]
    pcd_rotation = data["img_metas"]._data["pcd_rotation"]
    sample_idx = data["img_metas"]._data["sample_idx"]
    expected_rotation = np.array(
        [
            [0.99654, 0.08311407, 0.0],
            [-0.08311407, 0.99654, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    assert file_name == "./tests/data/scannet/points/scene0000_00.bin"
    assert np.allclose(pcd_rotation, expected_rotation, 1e-3)
    assert sample_idx == "scene0000_00"
    expected_points = torch.tensor(
        [
            [1.8339e00, 2.1093e00, 2.2900e00, 2.3895e00],
            [3.6079e00, 1.4592e-01, 2.0687e00, 2.1682e00],
            [4.1886e00, 5.0614e00, -1.0841e-01, -8.8736e-03],
            [6.8790e00, 1.5086e00, -9.3154e-02, 6.3816e-03],
            [4.8253e00, 2.6668e-01, 1.4917e00, 1.5912e00],
        ]
    )
    expected_gt_bboxes_3d = torch.tensor(
        [
            [-1.1835, -3.6317, 1.5704, 1.7577, 0.3761, 0.5724, 0.0000],
            [-3.1832, 3.2269, 1.1911, 0.6727, 0.2251, 0.6715, 0.0000],
            [-0.9598, -2.2864, 0.0093, 0.7506, 2.5709, 1.2145, 0.0000],
            [-2.6988, -2.7354, 0.8288, 0.7680, 1.8877, 0.2870, 0.0000],
            [3.2989, 0.2885, -0.0090, 0.7600, 3.8814, 2.1603, 0.0000],
        ]
    )
    expected_gt_labels = np.array(
        [
            6,
            6,
            4,
            9,
            11,
            11,
            10,
            0,
            15,
            17,
            17,
            17,
            3,
            12,
            4,
            4,
            14,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            5,
            5,
            5,
        ]
    )
    expected_pts_semantic_mask = np.array([0, 18, 18, 18, 18])
    expected_pts_instance_mask = np.array([44, 22, 10, 10, 57])
    original_classes = scannet_dataset.CLASSES

    assert scannet_dataset.CLASSES == class_names
    assert torch.allclose(points, expected_points, 1e-2)
    assert gt_bboxes_3d.tensor[:5].shape == (5, 7)
    assert torch.allclose(gt_bboxes_3d.tensor[:5], expected_gt_bboxes_3d, 1e-2)
    assert np.all(gt_labels.numpy() == expected_gt_labels)
    assert np.all(pts_semantic_mask.numpy() == expected_pts_semantic_mask)
    assert np.all(pts_instance_mask.numpy() == expected_pts_instance_mask)
    assert original_classes == class_names

    scannet_dataset = ScanNetDataset(
        root_path, ann_file, pipeline=None, classes=["cabinet", "bed"]
    )
    assert scannet_dataset.CLASSES != original_classes
    assert scannet_dataset.CLASSES == ["cabinet", "bed"]

    scannet_dataset = ScanNetDataset(
        root_path, ann_file, pipeline=None, classes=("cabinet", "bed")
    )
    assert scannet_dataset.CLASSES != original_classes
    assert scannet_dataset.CLASSES == ("cabinet", "bed")

    # Test load classes from file
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        path = tmpdir + "classes.txt"
        with open(path, "w") as f:
            f.write("cabinet\nbed\n")

    scannet_dataset = ScanNetDataset(
        root_path, ann_file, pipeline=None, classes=path
    )
    assert scannet_dataset.CLASSES != original_classes
    assert scannet_dataset.CLASSES == ["cabinet", "bed"]


def test_evaluate():
    if not torch.cuda.is_available():
        pytest.skip()
    from mmdet3d.core.bbox.structures import DepthInstance3DBoxes

    root_path = "./tests/data/scannet"
    ann_file = "./tests/data/scannet/scannet_infos.pkl"
    scannet_dataset = ScanNetDataset(root_path, ann_file)
    results = []
    pred_boxes = dict()
    pred_boxes["boxes_3d"] = DepthInstance3DBoxes(
        torch.tensor(
            [
                [
                    1.4813e00,
                    3.5207e00,
                    1.5704e00,
                    1.7445e00,
                    2.3196e-01,
                    5.7235e-01,
                    0.0000e00,
                ],
                [
                    2.9040e00,
                    -3.4803e00,
                    1.1911e00,
                    6.6078e-01,
                    1.7072e-01,
                    6.7154e-01,
                    0.0000e00,
                ],
                [
                    1.1466e00,
                    2.1987e00,
                    9.2576e-03,
                    5.4184e-01,
                    2.5346e00,
                    1.2145e00,
                    0.0000e00,
                ],
                [
                    2.9168e00,
                    2.5016e00,
                    8.2875e-01,
                    6.1697e-01,
                    1.8428e00,
                    2.8697e-01,
                    0.0000e00,
                ],
                [
                    -3.3114e00,
                    -1.3351e-02,
                    -8.9524e-03,
                    4.4082e-01,
                    3.8582e00,
                    2.1603e00,
                    0.0000e00,
                ],
                [
                    -2.0135e00,
                    -3.4857e00,
                    9.3848e-01,
                    1.9911e00,
                    2.1603e-01,
                    1.2767e00,
                    0.0000e00,
                ],
                [
                    -2.1945e00,
                    -3.1402e00,
                    -3.8165e-02,
                    1.4801e00,
                    6.8676e-01,
                    1.0586e00,
                    0.0000e00,
                ],
                [
                    -2.7553e00,
                    2.4055e00,
                    -2.9972e-02,
                    1.4764e00,
                    1.4927e00,
                    2.3380e00,
                    0.0000e00,
                ],
            ]
        )
    )
    pred_boxes["labels_3d"] = torch.tensor([6, 6, 4, 9, 11, 11])
    pred_boxes["scores_3d"] = torch.tensor([0.5, 1.0, 1.0, 1.0, 1.0, 0.5])
    results.append(pred_boxes)
    metric = [0.25, 0.5]
    ret_dict = scannet_dataset.evaluate(results, metric)
    assert abs(ret_dict["table_AP_0.25"] - 0.3333) < 0.01
    assert abs(ret_dict["window_AP_0.25"] - 1.0) < 0.01
    assert abs(ret_dict["counter_AP_0.25"] - 1.0) < 0.01
    assert abs(ret_dict["curtain_AP_0.25"] - 1.0) < 0.01

    # test evaluate with pipeline
    class_names = (
        "cabinet",
        "bed",
        "chair",
        "sofa",
        "table",
        "door",
        "window",
        "bookshelf",
        "picture",
        "counter",
        "desk",
        "curtain",
        "refrigerator",
        "showercurtrain",
        "toilet",
        "sink",
        "bathtub",
        "garbagebin",
    )
    eval_pipeline = [
        dict(
            type="LoadPointsFromFile",
            coord_type="DEPTH",
            shift_height=False,
            load_dim=6,
            use_dim=[0, 1, 2],
        ),
        dict(type="GlobalAlignment", rotation_axis=2),
        dict(
            type="DefaultFormatBundle3D",
            class_names=class_names,
            with_label=False,
        ),
        dict(type="Collect3D", keys=["points"]),
    ]
    ret_dict = scannet_dataset.evaluate(
        results, metric, pipeline=eval_pipeline
    )
    assert abs(ret_dict["table_AP_0.25"] - 0.3333) < 0.01
    assert abs(ret_dict["window_AP_0.25"] - 1.0) < 0.01
    assert abs(ret_dict["counter_AP_0.25"] - 1.0) < 0.01
    assert abs(ret_dict["curtain_AP_0.25"] - 1.0) < 0.01


def test_show():
    import tempfile
    from os import path as osp

    import mmcv

    from mmdet3d.core.bbox import DepthInstance3DBoxes

    tmp_dir = tempfile.TemporaryDirectory()
    temp_dir = tmp_dir.name
    root_path = "./tests/data/scannet"
    ann_file = "./tests/data/scannet/scannet_infos.pkl"
    scannet_dataset = ScanNetDataset(root_path, ann_file)
    boxes_3d = DepthInstance3DBoxes(
        torch.tensor(
            [
                [
                    -2.4053e00,
                    9.2295e-01,
                    8.0661e-02,
                    2.4054e00,
                    2.1468e00,
                    8.5990e-01,
                    0.0000e00,
                ],
                [
                    -1.9341e00,
                    -2.0741e00,
                    3.0698e-03,
                    3.2206e-01,
                    2.5322e-01,
                    3.5144e-01,
                    0.0000e00,
                ],
                [
                    -3.6908e00,
                    8.0684e-03,
                    2.6201e-01,
                    4.1515e-01,
                    7.6489e-01,
                    5.3585e-01,
                    0.0000e00,
                ],
                [
                    2.6332e00,
                    8.5143e-01,
                    -4.9964e-03,
                    3.0367e-01,
                    1.3448e00,
                    1.8329e00,
                    0.0000e00,
                ],
                [
                    2.0221e-02,
                    2.6153e00,
                    1.5109e-02,
                    7.3335e-01,
                    1.0429e00,
                    1.0251e00,
                    0.0000e00,
                ],
            ]
        )
    )
    scores_3d = torch.tensor(
        [1.2058e-04, 2.3012e-03, 6.2324e-06, 6.6139e-06, 6.7965e-05]
    )
    labels_3d = torch.tensor([0, 0, 0, 0, 0])
    result = dict(boxes_3d=boxes_3d, scores_3d=scores_3d, labels_3d=labels_3d)
    results = [result]
    scannet_dataset.show(results, temp_dir, show=False)
    pts_file_path = osp.join(
        temp_dir, "scene0000_00", "scene0000_00_points.obj"
    )
    gt_file_path = osp.join(temp_dir, "scene0000_00", "scene0000_00_gt.obj")
    pred_file_path = osp.join(
        temp_dir, "scene0000_00", "scene0000_00_pred.obj"
    )
    mmcv.check_file_exist(pts_file_path)
    mmcv.check_file_exist(gt_file_path)
    mmcv.check_file_exist(pred_file_path)
    tmp_dir.cleanup()

    # show function with pipeline
    class_names = (
        "cabinet",
        "bed",
        "chair",
        "sofa",
        "table",
        "door",
        "window",
        "bookshelf",
        "picture",
        "counter",
        "desk",
        "curtain",
        "refrigerator",
        "showercurtrain",
        "toilet",
        "sink",
        "bathtub",
        "garbagebin",
    )
    eval_pipeline = [
        dict(
            type="LoadPointsFromFile",
            coord_type="DEPTH",
            shift_height=False,
            load_dim=6,
            use_dim=[0, 1, 2],
        ),
        dict(type="GlobalAlignment", rotation_axis=2),
        dict(
            type="DefaultFormatBundle3D",
            class_names=class_names,
            with_label=False,
        ),
        dict(type="Collect3D", keys=["points"]),
    ]
    tmp_dir = tempfile.TemporaryDirectory()
    temp_dir = tmp_dir.name
    scannet_dataset.show(results, temp_dir, show=False, pipeline=eval_pipeline)
    pts_file_path = osp.join(
        temp_dir, "scene0000_00", "scene0000_00_points.obj"
    )
    gt_file_path = osp.join(temp_dir, "scene0000_00", "scene0000_00_gt.obj")
    pred_file_path = osp.join(
        temp_dir, "scene0000_00", "scene0000_00_pred.obj"
    )
    mmcv.check_file_exist(pts_file_path)
    mmcv.check_file_exist(gt_file_path)
    mmcv.check_file_exist(pred_file_path)
    tmp_dir.cleanup()


def test_seg_getitem():
    np.random.seed(0)
    root_path = "./tests/data/scannet/"
    ann_file = "./tests/data/scannet/scannet_infos.pkl"
    class_names = (
        "wall",
        "floor",
        "cabinet",
        "bed",
        "chair",
        "sofa",
        "table",
        "door",
        "window",
        "bookshelf",
        "picture",
        "counter",
        "desk",
        "curtain",
        "refrigerator",
        "showercurtrain",
        "toilet",
        "sink",
        "bathtub",
        "otherfurniture",
    )
    palette = [
        [174, 199, 232],
        [152, 223, 138],
        [31, 119, 180],
        [255, 187, 120],
        [188, 189, 34],
        [140, 86, 75],
        [255, 152, 150],
        [214, 39, 40],
        [197, 176, 213],
        [148, 103, 189],
        [196, 156, 148],
        [23, 190, 207],
        [247, 182, 210],
        [219, 219, 141],
        [255, 127, 14],
        [158, 218, 229],
        [44, 160, 44],
        [112, 128, 144],
        [227, 119, 194],
        [82, 84, 163],
    ]
    scene_idxs = [0 for _ in range(20)]

    # test network inputs are (xyz, rgb, normalized_xyz)
    pipelines = [
        dict(
            type="LoadPointsFromFile",
            coord_type="DEPTH",
            shift_height=False,
            use_color=True,
            load_dim=6,
            use_dim=[0, 1, 2, 3, 4, 5],
        ),
        dict(
            type="LoadAnnotations3D",
            with_bbox_3d=False,
            with_label_3d=False,
            with_mask_3d=False,
            with_seg_3d=True,
        ),
        dict(
            type="PointSegClassMapping",
            valid_cat_ids=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                14,
                16,
                24,
                28,
                33,
                34,
                36,
                39,
            ),
            max_cat_id=40,
        ),
        dict(
            type="IndoorPatchPointSample",
            num_points=5,
            block_size=1.5,
            ignore_index=len(class_names),
            use_normalized_coord=True,
            enlarge_size=0.2,
            min_unique_num=None,
        ),
        dict(type="NormalizePointsColor", color_mean=None),
        dict(type="DefaultFormatBundle3D", class_names=class_names),
        dict(
            type="Collect3D",
            keys=["points", "pts_semantic_mask"],
            meta_keys=["file_name", "sample_idx"],
        ),
    ]

    scannet_dataset = ScanNetSegDataset(
        data_root=root_path,
        ann_file=ann_file,
        pipeline=pipelines,
        classes=None,
        palette=None,
        modality=None,
        test_mode=False,
        ignore_index=None,
        scene_idxs=scene_idxs,
    )

    data = scannet_dataset[0]
    points = data["points"]._data
    pts_semantic_mask = data["pts_semantic_mask"]._data
    file_name = data["img_metas"]._data["file_name"]
    sample_idx = data["img_metas"]._data["sample_idx"]

    assert file_name == "./tests/data/scannet/points/scene0000_00.bin"
    assert sample_idx == "scene0000_00"
    expected_points = torch.tensor(
        [
            [
                0.0000,
                0.0000,
                1.2427,
                0.6118,
                0.5529,
                0.4471,
                -0.6462,
                -1.0046,
                0.4280,
            ],
            [
                0.1553,
                -0.0074,
                1.6077,
                0.5882,
                0.6157,
                0.5569,
                -0.6001,
                -1.0068,
                0.5537,
            ],
            [
                0.1518,
                0.6016,
                0.6548,
                0.1490,
                0.1059,
                0.0431,
                -0.6012,
                -0.8309,
                0.2255,
            ],
            [
                -0.7494,
                0.1033,
                0.6756,
                0.5216,
                0.4353,
                0.3333,
                -0.8687,
                -0.9748,
                0.2327,
            ],
            [
                -0.6836,
                -0.0203,
                0.5884,
                0.5765,
                0.5020,
                0.4510,
                -0.8491,
                -1.0105,
                0.2027,
            ],
        ]
    )
    expected_pts_semantic_mask = np.array([13, 13, 12, 2, 0])
    original_classes = scannet_dataset.CLASSES
    original_palette = scannet_dataset.PALETTE

    assert scannet_dataset.CLASSES == class_names
    assert scannet_dataset.ignore_index == 20
    assert torch.allclose(points, expected_points, 1e-2)
    assert np.all(pts_semantic_mask.numpy() == expected_pts_semantic_mask)
    assert original_classes == class_names
    assert original_palette == palette
    assert scannet_dataset.scene_idxs.dtype == np.int32
    assert np.all(scannet_dataset.scene_idxs == np.array(scene_idxs))

    # test network inputs are (xyz, rgb)
    np.random.seed(0)
    new_pipelines = copy.deepcopy(pipelines)
    new_pipelines[3] = dict(
        type="IndoorPatchPointSample",
        num_points=5,
        block_size=1.5,
        ignore_index=len(class_names),
        use_normalized_coord=False,
        enlarge_size=0.2,
        min_unique_num=None,
    )
    scannet_dataset = ScanNetSegDataset(
        data_root=root_path,
        ann_file=ann_file,
        pipeline=new_pipelines,
        scene_idxs=scene_idxs,
    )

    data = scannet_dataset[0]
    points = data["points"]._data
    assert torch.allclose(points, expected_points[:, :6], 1e-2)

    # test network inputs are (xyz, normalized_xyz)
    np.random.seed(0)
    new_pipelines = copy.deepcopy(pipelines)
    new_pipelines[0] = dict(
        type="LoadPointsFromFile",
        coord_type="DEPTH",
        shift_height=False,
        use_color=False,
        load_dim=6,
        use_dim=[0, 1, 2],
    )
    new_pipelines.remove(new_pipelines[4])
    scannet_dataset = ScanNetSegDataset(
        data_root=root_path,
        ann_file=ann_file,
        pipeline=new_pipelines,
        scene_idxs=scene_idxs,
    )

    data = scannet_dataset[0]
    points = data["points"]._data
    assert torch.allclose(points, expected_points[:, [0, 1, 2, 6, 7, 8]], 1e-2)

    # test network inputs are (xyz,)
    np.random.seed(0)
    new_pipelines = copy.deepcopy(pipelines)
    new_pipelines[0] = dict(
        type="LoadPointsFromFile",
        coord_type="DEPTH",
        shift_height=False,
        use_color=False,
        load_dim=6,
        use_dim=[0, 1, 2],
    )
    new_pipelines[3] = dict(
        type="IndoorPatchPointSample",
        num_points=5,
        block_size=1.5,
        ignore_index=len(class_names),
        use_normalized_coord=False,
        enlarge_size=0.2,
        min_unique_num=None,
    )
    new_pipelines.remove(new_pipelines[4])
    scannet_dataset = ScanNetSegDataset(
        data_root=root_path,
        ann_file=ann_file,
        pipeline=new_pipelines,
        scene_idxs=scene_idxs,
    )

    data = scannet_dataset[0]
    points = data["points"]._data
    assert torch.allclose(points, expected_points[:, :3], 1e-2)

    # test dataset with selected classes
    scannet_dataset = ScanNetSegDataset(
        data_root=root_path,
        ann_file=ann_file,
        pipeline=None,
        classes=["cabinet", "chair"],
        scene_idxs=scene_idxs,
    )

    label_map = {i: 20 for i in range(41)}
    label_map.update({3: 0, 5: 1})

    assert scannet_dataset.CLASSES != original_classes
    assert scannet_dataset.CLASSES == ["cabinet", "chair"]
    assert scannet_dataset.PALETTE == [palette[2], palette[4]]
    assert scannet_dataset.VALID_CLASS_IDS == [3, 5]
    assert scannet_dataset.label_map == label_map
    assert scannet_dataset.label2cat == {0: "cabinet", 1: "chair"}

    # test load classes from file
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        path = tmpdir + "classes.txt"
        with open(path, "w") as f:
            f.write("cabinet\nchair\n")

    scannet_dataset = ScanNetSegDataset(
        data_root=root_path,
        ann_file=ann_file,
        pipeline=None,
        classes=path,
        scene_idxs=scene_idxs,
    )
    assert scannet_dataset.CLASSES != original_classes
    assert scannet_dataset.CLASSES == ["cabinet", "chair"]
    assert scannet_dataset.PALETTE == [palette[2], palette[4]]
    assert scannet_dataset.VALID_CLASS_IDS == [3, 5]
    assert scannet_dataset.label_map == label_map
    assert scannet_dataset.label2cat == {0: "cabinet", 1: "chair"}

    # test scene_idxs in dataset
    # we should input scene_idxs in train mode
    with pytest.raises(NotImplementedError):
        scannet_dataset = ScanNetSegDataset(
            data_root=root_path,
            ann_file=ann_file,
            pipeline=None,
            scene_idxs=None,
        )

    # test mode
    scannet_dataset = ScanNetSegDataset(
        data_root=root_path,
        ann_file=ann_file,
        pipeline=None,
        test_mode=True,
        scene_idxs=scene_idxs,
    )
    assert np.all(scannet_dataset.scene_idxs == np.array([0]))


def test_seg_evaluate():
    if not torch.cuda.is_available():
        pytest.skip()
    root_path = "./tests/data/scannet"
    ann_file = "./tests/data/scannet/scannet_infos.pkl"
    scannet_dataset = ScanNetSegDataset(
        data_root=root_path, ann_file=ann_file, test_mode=True
    )
    results = []
    pred_sem_mask = dict(
        semantic_mask=torch.tensor(
            [
                13,
                5,
                1,
                2,
                6,
                2,
                13,
                1,
                14,
                2,
                0,
                0,
                5,
                5,
                3,
                0,
                1,
                14,
                0,
                0,
                0,
                18,
                6,
                15,
                13,
                0,
                2,
                4,
                0,
                3,
                16,
                6,
                13,
                5,
                13,
                0,
                0,
                0,
                0,
                1,
                7,
                3,
                19,
                12,
                8,
                0,
                11,
                0,
                0,
                1,
                2,
                13,
                17,
                1,
                1,
                1,
                6,
                2,
                13,
                19,
                4,
                17,
                0,
                14,
                1,
                7,
                2,
                1,
                7,
                2,
                0,
                5,
                17,
                5,
                0,
                0,
                3,
                6,
                5,
                11,
                1,
                13,
                13,
                2,
                3,
                1,
                0,
                13,
                19,
                1,
                14,
                5,
                3,
                1,
                13,
                1,
                2,
                3,
                2,
                1,
            ]
        ).long()
    )
    results.append(pred_sem_mask)

    class_names = (
        "wall",
        "floor",
        "cabinet",
        "bed",
        "chair",
        "sofa",
        "table",
        "door",
        "window",
        "bookshelf",
        "picture",
        "counter",
        "desk",
        "curtain",
        "refrigerator",
        "showercurtrain",
        "toilet",
        "sink",
        "bathtub",
        "otherfurniture",
    )
    eval_pipeline = [
        dict(
            type="LoadPointsFromFile",
            coord_type="DEPTH",
            shift_height=False,
            use_color=True,
            load_dim=6,
            use_dim=[0, 1, 2, 3, 4, 5],
        ),
        dict(
            type="LoadAnnotations3D",
            with_bbox_3d=False,
            with_label_3d=False,
            with_mask_3d=False,
            with_seg_3d=True,
        ),
        dict(
            type="PointSegClassMapping",
            valid_cat_ids=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                14,
                16,
                24,
                28,
                33,
                34,
                36,
                39,
            ),
            max_cat_id=40,
        ),
        dict(type="DefaultFormatBundle3D", class_names=class_names),
        dict(type="Collect3D", keys=["points", "pts_semantic_mask"]),
    ]
    ret_dict = scannet_dataset.evaluate(results, pipeline=eval_pipeline)
    assert abs(ret_dict["miou"] - 0.5308) < 0.01
    assert abs(ret_dict["acc"] - 0.8219) < 0.01
    assert abs(ret_dict["acc_cls"] - 0.7649) < 0.01


def test_seg_show():
    import tempfile
    from os import path as osp

    import mmcv

    tmp_dir = tempfile.TemporaryDirectory()
    temp_dir = tmp_dir.name
    root_path = "./tests/data/scannet"
    ann_file = "./tests/data/scannet/scannet_infos.pkl"
    scannet_dataset = ScanNetSegDataset(
        data_root=root_path, ann_file=ann_file, scene_idxs=[0]
    )
    result = dict(
        semantic_mask=torch.tensor(
            [
                13,
                5,
                1,
                2,
                6,
                2,
                13,
                1,
                14,
                2,
                0,
                0,
                5,
                5,
                3,
                0,
                1,
                14,
                0,
                0,
                0,
                18,
                6,
                15,
                13,
                0,
                2,
                4,
                0,
                3,
                16,
                6,
                13,
                5,
                13,
                0,
                0,
                0,
                0,
                1,
                7,
                3,
                19,
                12,
                8,
                0,
                11,
                0,
                0,
                1,
                2,
                13,
                17,
                1,
                1,
                1,
                6,
                2,
                13,
                19,
                4,
                17,
                0,
                14,
                1,
                7,
                2,
                1,
                7,
                2,
                0,
                5,
                17,
                5,
                0,
                0,
                3,
                6,
                5,
                11,
                1,
                13,
                13,
                2,
                3,
                1,
                0,
                13,
                19,
                1,
                14,
                5,
                3,
                1,
                13,
                1,
                2,
                3,
                2,
                1,
            ]
        ).long()
    )
    results = [result]
    scannet_dataset.show(results, temp_dir, show=False)
    pts_file_path = osp.join(
        temp_dir, "scene0000_00", "scene0000_00_points.obj"
    )
    gt_file_path = osp.join(temp_dir, "scene0000_00", "scene0000_00_gt.obj")
    pred_file_path = osp.join(
        temp_dir, "scene0000_00", "scene0000_00_pred.obj"
    )
    mmcv.check_file_exist(pts_file_path)
    mmcv.check_file_exist(gt_file_path)
    mmcv.check_file_exist(pred_file_path)
    tmp_dir.cleanup()
    # test show with pipeline
    tmp_dir = tempfile.TemporaryDirectory()
    temp_dir = tmp_dir.name
    class_names = (
        "wall",
        "floor",
        "cabinet",
        "bed",
        "chair",
        "sofa",
        "table",
        "door",
        "window",
        "bookshelf",
        "picture",
        "counter",
        "desk",
        "curtain",
        "refrigerator",
        "showercurtrain",
        "toilet",
        "sink",
        "bathtub",
        "otherfurniture",
    )
    eval_pipeline = [
        dict(
            type="LoadPointsFromFile",
            coord_type="DEPTH",
            shift_height=False,
            use_color=True,
            load_dim=6,
            use_dim=[0, 1, 2, 3, 4, 5],
        ),
        dict(
            type="LoadAnnotations3D",
            with_bbox_3d=False,
            with_label_3d=False,
            with_mask_3d=False,
            with_seg_3d=True,
        ),
        dict(
            type="PointSegClassMapping",
            valid_cat_ids=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                14,
                16,
                24,
                28,
                33,
                34,
                36,
                39,
            ),
            max_cat_id=40,
        ),
        dict(type="DefaultFormatBundle3D", class_names=class_names),
        dict(type="Collect3D", keys=["points", "pts_semantic_mask"]),
    ]
    scannet_dataset.show(results, temp_dir, show=False, pipeline=eval_pipeline)
    pts_file_path = osp.join(
        temp_dir, "scene0000_00", "scene0000_00_points.obj"
    )
    gt_file_path = osp.join(temp_dir, "scene0000_00", "scene0000_00_gt.obj")
    pred_file_path = osp.join(
        temp_dir, "scene0000_00", "scene0000_00_pred.obj"
    )
    mmcv.check_file_exist(pts_file_path)
    mmcv.check_file_exist(gt_file_path)
    mmcv.check_file_exist(pred_file_path)
    tmp_dir.cleanup()


def test_seg_format_results():
    from os import path as osp

    import mmcv

    root_path = "./tests/data/scannet"
    ann_file = "./tests/data/scannet/scannet_infos.pkl"
    scannet_dataset = ScanNetSegDataset(
        data_root=root_path, ann_file=ann_file, test_mode=True
    )
    results = []
    pred_sem_mask = dict(
        semantic_mask=torch.tensor(
            [
                13,
                5,
                1,
                2,
                6,
                2,
                13,
                1,
                14,
                2,
                0,
                0,
                5,
                5,
                3,
                0,
                1,
                14,
                0,
                0,
                0,
                18,
                6,
                15,
                13,
                0,
                2,
                4,
                0,
                3,
                16,
                6,
                13,
                5,
                13,
                0,
                0,
                0,
                0,
                1,
                7,
                3,
                19,
                12,
                8,
                0,
                11,
                0,
                0,
                1,
                2,
                13,
                17,
                1,
                1,
                1,
                6,
                2,
                13,
                19,
                4,
                17,
                0,
                14,
                1,
                7,
                2,
                1,
                7,
                2,
                0,
                5,
                17,
                5,
                0,
                0,
                3,
                6,
                5,
                11,
                1,
                13,
                13,
                2,
                3,
                1,
                0,
                13,
                19,
                1,
                14,
                5,
                3,
                1,
                13,
                1,
                2,
                3,
                2,
                1,
            ]
        ).long()
    )
    results.append(pred_sem_mask)
    result_files, tmp_dir = scannet_dataset.format_results(results)

    expected_label = np.array(
        [
            16,
            6,
            2,
            3,
            7,
            3,
            16,
            2,
            24,
            3,
            1,
            1,
            6,
            6,
            4,
            1,
            2,
            24,
            1,
            1,
            1,
            36,
            7,
            28,
            16,
            1,
            3,
            5,
            1,
            4,
            33,
            7,
            16,
            6,
            16,
            1,
            1,
            1,
            1,
            2,
            8,
            4,
            39,
            14,
            9,
            1,
            12,
            1,
            1,
            2,
            3,
            16,
            34,
            2,
            2,
            2,
            7,
            3,
            16,
            39,
            5,
            34,
            1,
            24,
            2,
            8,
            3,
            2,
            8,
            3,
            1,
            6,
            34,
            6,
            1,
            1,
            4,
            7,
            6,
            12,
            2,
            16,
            16,
            3,
            4,
            2,
            1,
            16,
            39,
            2,
            24,
            6,
            4,
            2,
            16,
            2,
            3,
            4,
            3,
            2,
        ]
    )
    expected_txt_path = osp.join(tmp_dir.name, "results", "scene0000_00.txt")
    assert np.all(result_files[0]["seg_mask"] == expected_label)
    mmcv.check_file_exist(expected_txt_path)


def test_instance_seg_getitem():
    np.random.seed(0)
    root_path = "./tests/data/scannet/"
    ann_file = "./tests/data/scannet/scannet_infos.pkl"
    class_names = (
        "cabinet",
        "bed",
        "chair",
        "sofa",
        "table",
        "door",
        "window",
        "bookshelf",
        "picture",
        "counter",
        "desk",
        "curtain",
        "refrigerator",
        "showercurtrain",
        "toilet",
        "sink",
        "bathtub",
        "garbagebin",
    )
    train_pipeline = [
        dict(
            type="LoadPointsFromFile",
            coord_type="DEPTH",
            shift_height=False,
            use_color=True,
            load_dim=6,
            use_dim=[0, 1, 2, 3, 4, 5],
        ),
        dict(
            type="LoadAnnotations3D",
            with_bbox_3d=False,
            with_label_3d=False,
            with_mask_3d=True,
            with_seg_3d=True,
        ),
        dict(
            type="PointSegClassMapping",
            valid_cat_ids=(
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                14,
                16,
                24,
                28,
                33,
                34,
                36,
                39,
            ),
            max_cat_id=40,
        ),
        dict(type="NormalizePointsColor", color_mean=None),
        dict(type="DefaultFormatBundle3D", class_names=class_names),
        dict(
            type="Collect3D",
            keys=["points", "pts_semantic_mask", "pts_instance_mask"],
        ),
    ]
    scannet_dataset = ScanNetInstanceSegDataset(
        data_root=root_path,
        ann_file=ann_file,
        pipeline=train_pipeline,
        classes=class_names,
        test_mode=False,
    )
    expected_points = torch.tensor(
        [
            [
                -3.4742e00,
                7.8792e-01,
                1.7397e00,
                3.3725e-01,
                3.5294e-01,
                3.0588e-01,
            ],
            [
                2.7216e00,
                3.4164e00,
                2.4572e00,
                6.6275e-01,
                6.2745e-01,
                5.1373e-01,
            ],
            [
                1.3404e00,
                -1.4675e00,
                -4.4059e-02,
                3.8431e-01,
                3.6078e-01,
                3.5686e-01,
            ],
            [
                -3.0335e00,
                2.7273e00,
                1.5181e00,
                2.3137e-01,
                1.6078e-01,
                8.2353e-02,
            ],
            [
                -4.3207e-01,
                1.8154e00,
                1.7455e-01,
                4.0392e-01,
                3.8039e-01,
                4.1961e-01,
            ],
        ]
    )

    data = scannet_dataset[0]

    points = data["points"]._data[:5]
    pts_semantic_mask = data["pts_semantic_mask"]._data[:5]
    pts_instance_mask = data["pts_instance_mask"]._data[:5]
    expected_semantic_mask = np.array([11, 18, 18, 0, 4])
    expected_instance_mask = np.array([6, 56, 10, 9, 35])

    assert torch.allclose(points, expected_points, 1e-2)
    assert np.all(pts_semantic_mask.numpy() == expected_semantic_mask)
    assert np.all(pts_instance_mask.numpy() == expected_instance_mask)


def test_instance_seg_evaluate():
    root_path = "./tests/data/scannet"
    ann_file = "./tests/data/scannet/scannet_infos.pkl"
    class_names = (
        "cabinet",
        "bed",
        "chair",
        "sofa",
        "table",
        "door",
        "window",
        "bookshelf",
        "picture",
        "counter",
        "desk",
        "curtain",
        "refrigerator",
        "showercurtrain",
        "toilet",
        "sink",
        "bathtub",
        "garbagebin",
    )
    test_pipeline = [
        dict(
            type="LoadPointsFromFile",
            coord_type="DEPTH",
            shift_height=False,
            use_color=True,
            load_dim=6,
            use_dim=[0, 1, 2, 3, 4, 5],
        ),
        dict(type="NormalizePointsColor", color_mean=None),
        dict(type="DefaultFormatBundle3D", class_names=class_names),
        dict(type="Collect3D", keys=["points"]),
    ]
    scannet_dataset = ScanNetInstanceSegDataset(
        data_root=root_path,
        ann_file=ann_file,
        pipeline=test_pipeline,
        test_mode=True,
    )

    pred_mask = torch.tensor(
        [
            1,
            -1,
            -1,
            -1,
            7,
            11,
            2,
            -1,
            1,
            10,
            -1,
            -1,
            5,
            -1,
            -1,
            -1,
            -1,
            1,
            -1,
            -1,
            -1,
            -1,
            0,
            -1,
            1,
            -1,
            12,
            -1,
            -1,
            -1,
            8,
            5,
            1,
            5,
            2,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            1,
            8,
            -1,
            -1,
            -1,
            0,
            4,
            3,
            -1,
            9,
            -1,
            -1,
            6,
            -1,
            -1,
            -1,
            -1,
            13,
            -1,
            -1,
            5,
            -1,
            5,
            -1,
            -1,
            9,
            0,
            5,
            -1,
            -1,
            2,
            3,
            4,
            -1,
            -1,
            -1,
            2,
            -1,
            -1,
            -1,
            5,
            9,
            -1,
            1,
            -1,
            4,
            10,
            4,
            -1,
        ]
    ).long()
    pred_labels = torch.tensor(
        [4, 11, 11, 10, 0, 3, 12, 4, 14, 1, 0, 0, 0, 5, 5]
    ).long()
    pred_scores = torch.tensor([0.99 for _ in range(len(pred_labels))])
    results = [
        dict(
            instance_mask=pred_mask,
            instance_label=pred_labels,
            instance_score=torch.tensor(pred_scores),
        )
    ]
    eval_pipeline = [
        dict(
            type="LoadPointsFromFile",
            coord_type="DEPTH",
            shift_height=False,
            use_color=True,
            load_dim=6,
            use_dim=[0, 1, 2, 3, 4, 5],
        ),
        dict(
            type="LoadAnnotations3D",
            with_bbox_3d=False,
            with_label_3d=False,
            with_mask_3d=True,
            with_seg_3d=True,
        ),
        dict(
            type="PointSegClassMapping",
            valid_cat_ids=(
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                14,
                16,
                24,
                28,
                33,
                34,
                36,
                39,
            ),
            max_cat_id=40,
        ),
        dict(type="NormalizePointsColor", color_mean=None),
        dict(type="DefaultFormatBundle3D", class_names=class_names),
        dict(
            type="Collect3D",
            keys=["points", "pts_semantic_mask", "pts_instance_mask"],
        ),
    ]
    # We add options here as default min_region_size
    # is much bigger than test instances.
    ret_dict = scannet_dataset.evaluate(
        results,
        pipeline=eval_pipeline,
        options=dict(min_region_sizes=np.array([1])),
    )
    assert abs(ret_dict["all_ap"] - 0.90625) < 0.001
    assert abs(ret_dict["all_ap_50%"] - 0.90625) < 0.001
    assert abs(ret_dict["all_ap_25%"] - 0.94444) < 0.001
    assert abs(ret_dict["classes"]["cabinet"]["ap25%"] - 1.0) < 0.001
    assert abs(ret_dict["classes"]["cabinet"]["ap50%"] - 0.65625) < 0.001
    assert abs(ret_dict["classes"]["door"]["ap25%"] - 0.5) < 0.001
    assert abs(ret_dict["classes"]["door"]["ap50%"] - 0.5) < 0.001
