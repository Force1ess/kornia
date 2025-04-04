# LICENSE HEADER MANAGED BY add-license-header
#
# Copyright 2018 Kornia Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from functools import partial

import pytest
import torch

from kornia.geometry.boxes import Boxes, Boxes3D

from testing.base import BaseTester


class TestBoxes2D(BaseTester):
    def test_smoke(self, device, dtype):
        def _create_tensor_box():
            # Sample two points of the rectangle
            points = torch.rand(1, 4, device=device, dtype=dtype)

            # Fill according missing points
            tensor_boxes = torch.zeros(1, 4, 2, device=device, dtype=dtype)
            tensor_boxes[0, 0] = points[0][:2]
            tensor_boxes[0, 1, 0] = points[0][2]
            tensor_boxes[0, 1, 1] = points[0][1]
            tensor_boxes[0, 2] = points[0][2:]
            tensor_boxes[0, 3, 0] = points[0][0]
            tensor_boxes[0, 3, 1] = points[0][3]
            return tensor_boxes

        # Validate
        assert Boxes(_create_tensor_box())  # Validate 1 box

        # 2 boxes without batching (N, 4, 2) where N=2
        two_boxes = torch.cat([_create_tensor_box(), _create_tensor_box()])
        assert Boxes(two_boxes)

        # 2 boxes in batch (B, 1, 4, 2) where B=2
        batched_bbox = torch.stack([_create_tensor_box(), _create_tensor_box()])
        assert Boxes(batched_bbox)

    def test_get_boxes_shape(self, device, dtype):
        box = Boxes(torch.tensor([[[1.0, 1.0], [3.0, 2.0], [1.0, 2.0], [3.0, 1.0]]], device=device, dtype=dtype))
        t_boxes = torch.tensor(
            [[[1.0, 1.0], [3.0, 1.0], [1.0, 2.0], [3.0, 2.0]], [[5.0, 4.0], [2.0, 2.0], [5.0, 2.0], [2.0, 4.0]]],
            device=device,
            dtype=dtype,
        )  # (2, 4, 2)
        boxes = Boxes(t_boxes)
        boxes_batch = Boxes(t_boxes[None])  # (1, 2, 4, 2)

        # Single box
        h, w = box.get_boxes_shape()
        assert (h.item(), w.item()) == (2, 3)

        # Boxes
        h, w = boxes.get_boxes_shape()
        assert h.ndim == 1
        assert w.ndim == 1
        assert len(h) == 2
        assert len(w) == 2
        self.assert_close(h, torch.as_tensor([2.0, 3.0], device=device, dtype=dtype))
        self.assert_close(w, torch.as_tensor([3.0, 4.0], device=device, dtype=dtype))

        # Box batch
        h, w = boxes_batch.get_boxes_shape()
        assert h.ndim == 2
        assert w.ndim == 2
        assert h.shape == (1, 2)
        assert w.shape == (1, 2)
        self.assert_close(h, torch.as_tensor([[2.0, 3.0]], device=device, dtype=dtype))
        self.assert_close(w, torch.as_tensor([[3.0, 4.0]], device=device, dtype=dtype))

    def test_get_boxes_shape_batch(self, device, dtype):
        t_box1 = torch.tensor([[[1.0, 1.0], [3.0, 2.0], [3.0, 1.0], [1.0, 2.0]]], device=device, dtype=dtype)
        t_box2 = torch.tensor([[[5.0, 2.0], [2.0, 2.0], [5.0, 4.0], [2.0, 4.0]]], device=device, dtype=dtype)
        batched_boxes = Boxes(torch.stack([t_box1, t_box2]))

        h, w = batched_boxes.get_boxes_shape()
        assert h.ndim == 2
        assert w.ndim == 2
        assert h.shape == (2, 1)
        assert w.shape == (2, 1)
        self.assert_close(h, torch.as_tensor([[2], [3]], device=device, dtype=dtype))
        self.assert_close(w, torch.as_tensor([[3], [4]], device=device, dtype=dtype))

    @pytest.mark.parametrize("shape", [(1, 4), (1, 1, 4)])
    def test_from_tensor(self, shape, device, dtype):
        box_xyxy = torch.as_tensor([[1, 2, 3, 4]], device=device, dtype=dtype).view(*shape)
        box_xyxy_plus = torch.as_tensor([[1, 2, 2, 3]], device=device, dtype=dtype).view(*shape)
        box_xywh = torch.as_tensor([[1, 2, 2, 2]], device=device, dtype=dtype).view(*shape)
        box_vertices = torch.as_tensor([[[1, 2], [3, 2], [3, 4], [1, 4]]], device=device, dtype=dtype).view(*shape, 2)
        box_vertices_plus = torch.as_tensor([[[1, 2], [2, 2], [2, 3], [1, 3]]], device=device, dtype=dtype).view(
            *shape, 2
        )

        expected_box = torch.as_tensor([[[1, 2], [2, 2], [2, 3], [1, 3]]], device=device, dtype=dtype).view(*shape, 2)

        boxes_xyxy = Boxes.from_tensor(box_xyxy, mode="xyxy").data
        boxes_xyxy_plus = Boxes.from_tensor(box_xyxy_plus, mode="xyxy_plus").data
        boxes_xywh = Boxes.from_tensor(box_xywh, mode="xywh").data
        box_vertices = Boxes.from_tensor(box_vertices, mode="vertices").data
        boxes_vertices_plus = Boxes.from_tensor(box_vertices_plus, mode="vertices_plus").data

        assert boxes_xyxy.shape == expected_box.shape
        self.assert_close(boxes_xyxy, expected_box)

        assert boxes_xyxy_plus.shape == expected_box.shape
        self.assert_close(boxes_xyxy_plus, expected_box)

        assert boxes_xywh.shape == expected_box.shape
        self.assert_close(boxes_xywh, expected_box)

        assert box_vertices.shape == expected_box.shape
        self.assert_close(box_vertices, expected_box)

        assert boxes_vertices_plus.shape == expected_box.shape
        self.assert_close(boxes_vertices_plus, expected_box)

    @pytest.mark.parametrize("shape", [(1, 4), (1, 1, 4)])
    def test_from_invalid_tensor(self, shape, device, dtype):
        box_xyxy = torch.as_tensor([[1, 2, -3, 4]], device=device, dtype=dtype).view(*shape)  # Invalid width
        box_xyxy_plus = torch.as_tensor([[1, 2, 0, 3]], device=device, dtype=dtype).view(*shape)  # Invalid height

        try:
            Boxes.from_tensor(box_xyxy, mode="xyxy")
            raise AssertionError("Boxes.from_tensor should have raised any exception")
        except ValueError:
            pass

        try:
            Boxes.from_tensor(box_xyxy_plus, mode="xyxy_plus")
            raise AssertionError("Boxes.from_tensor should have raised any exception")
        except ValueError:
            pass

    @pytest.mark.parametrize("shape", [(1, 4), (1, 1, 4)])
    def test_boxes_to_tensor(self, shape, device, dtype):
        # quadrilateral with randomized vertices to reflect possible transforms.
        box = Boxes(torch.as_tensor([[[2, 2], [2, 3], [1, 3], [1, 2]]], device=device, dtype=dtype).view(*shape, 2))

        expected_box_xyxy = torch.as_tensor([[1, 2, 3, 4]], device=device, dtype=dtype).view(*shape)
        expected_box_xyxy_plus = torch.as_tensor([[1, 2, 2, 3]], device=device, dtype=dtype).view(*shape)
        expected_box_xywh = torch.as_tensor([[1, 2, 2, 2]], device=device, dtype=dtype).view(*shape)
        expected_vertices = torch.as_tensor([[[1, 2], [3, 2], [3, 4], [1, 4]]], device=device, dtype=dtype).view(
            *shape, 2
        )
        expected_vertices_plus = torch.as_tensor([[[1, 2], [2, 2], [2, 3], [1, 3]]], device=device, dtype=dtype).view(
            *shape, 2
        )

        boxes_xyxy = box.to_tensor(mode="xyxy")
        boxes_xyxy_plus = box.to_tensor(mode="xyxy_plus")
        boxes_xywh = box.to_tensor(mode="xywh")
        boxes_vertices = box.to_tensor(mode="vertices")
        boxes_vertices_plus = box.to_tensor(mode="vertices_plus")

        assert boxes_xyxy.shape == expected_box_xyxy.shape
        self.assert_close(boxes_xyxy, expected_box_xyxy)

        assert boxes_xyxy_plus.shape == expected_box_xyxy_plus.shape
        self.assert_close(boxes_xyxy_plus, expected_box_xyxy_plus)

        assert boxes_xywh.shape == expected_box_xywh.shape
        self.assert_close(boxes_xywh, expected_box_xywh)

        assert boxes_vertices.shape == expected_vertices.shape
        self.assert_close(boxes_vertices, expected_vertices)

        assert boxes_vertices_plus.shape == expected_vertices_plus.shape
        self.assert_close(boxes_vertices_plus, expected_vertices_plus)

    @pytest.mark.parametrize("mode", ["xyxy", "xyxy_plus", "xywh", "vertices", "vertices_plus"])
    def test_boxes_list_to_tensor_list(self, mode, device, dtype):
        src_1 = [
            torch.as_tensor([[[1, 2], [1, 3], [2, 2], [2, 3]]], device=device, dtype=dtype),
            torch.as_tensor(
                [[[1, 2], [1, 3], [2, 2], [2, 3]], [[1, 2], [1, 3], [2, 2], [2, 3]]], device=device, dtype=dtype
            ),
        ]
        src_2 = [
            torch.as_tensor([[1, 1, 5, 5]], device=device, dtype=dtype),
            torch.as_tensor([[1, 1, 5, 5], [1, 1, 5, 5]], device=device, dtype=dtype),
        ]
        src = src_1 if mode in ["vertices", "vertices_plus"] else src_2
        box = Boxes.from_tensor(src, mode=mode)
        out = box.to_tensor(mode)
        assert out[0].shape == src[0].shape
        assert out[1].shape == src[1].shape

    def test_boxes_to_mask(self, device, dtype):
        t_box1 = torch.tensor(
            [[[1.0, 1.0], [3.0, 1.0], [3.0, 2.0], [1.0, 2.0]]], device=device, dtype=dtype
        )  # (1, 4, 2)
        t_box2 = torch.tensor(
            [[[2.0, 2.0], [4.0, 2.0], [4.0, 5.0], [2.0, 4.0]]], device=device, dtype=dtype
        )  # (1, 4, 2)
        box1, box2 = Boxes(t_box1), Boxes(t_box2)
        two_boxes = Boxes(torch.cat([t_box1, t_box2]))  # (2, 4, 2)
        batched_boxes = Boxes(torch.stack([t_box1, t_box2]))  # (2, 1, 4, 2)

        height, width = 7, 5

        expected_mask1 = torch.tensor(
            [
                [
                    [0, 0, 0, 0, 0],
                    [0, 1, 1, 1, 0],
                    [0, 1, 1, 1, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                ]
            ],
            device=device,
            dtype=dtype,
        )

        expected_mask2 = torch.tensor(
            [
                [
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 1, 1, 1],
                    [0, 0, 1, 1, 1],
                    [0, 0, 1, 1, 1],
                    [0, 0, 1, 1, 1],
                    [0, 0, 0, 0, 0],
                ]
            ],
            device=device,
            dtype=dtype,
        )
        expected_two_masks = torch.cat([expected_mask1, expected_mask2])
        expected_batched_masks = torch.stack([expected_mask1, expected_mask2])

        mask1 = box1.to_mask(height, width)
        mask2 = box2.to_mask(height, width)
        two_masks = two_boxes.to_mask(height, width)
        batched_masks = batched_boxes.to_mask(height, width)

        assert mask1.shape == expected_mask1.shape
        self.assert_close(mask1, expected_mask1)

        assert mask2.shape == expected_mask2.shape
        self.assert_close(mask2, expected_mask2)

        assert two_masks.shape == expected_two_masks.shape
        self.assert_close(two_masks, expected_two_masks)

        assert batched_masks.shape == expected_batched_masks.shape
        self.assert_close(batched_masks, expected_batched_masks)

    def test_to(self, device, dtype):
        boxes = Boxes.from_tensor(torch.as_tensor([[1, 2, 3, 4]], device="cpu", dtype=torch.float32))
        assert boxes.to(device=device).data.device == device
        assert boxes.to(dtype=dtype).data.dtype == dtype

        boxes_moved = boxes.to(device, dtype)
        assert boxes_moved is boxes  # to is an inplace op.
        assert boxes_moved.data.device == device, boxes_moved.data.dtype == dtype

    def test_gradcheck(self, device):
        def apply_boxes_method(tensor: torch.Tensor, method: str, **kwargs):
            boxes = Boxes(tensor)
            result = getattr(boxes, method)(**kwargs)
            return result.data if isinstance(result, Boxes) else result

        t_boxes1 = torch.tensor([[[1.0, 1.0], [3.0, 1.0], [3.0, 2.0], [1.0, 2.0]]], device=device, dtype=torch.float64)

        t_boxes2 = t_boxes1.detach().clone()
        t_boxes3 = t_boxes1.detach().clone()
        t_boxes4 = t_boxes1.detach().clone()
        t_boxes_xyxy = torch.tensor([[1.0, 3.0, 5.0, 6.0]])
        t_boxes_xyxy1 = t_boxes_xyxy.detach().clone()

        self.gradcheck(partial(apply_boxes_method, method="to_tensor"), (t_boxes2,))
        self.gradcheck(partial(apply_boxes_method, method="to_tensor", mode="xyxy_plus"), (t_boxes3,))
        self.gradcheck(partial(apply_boxes_method, method="to_tensor", mode="vertices_plus"), (t_boxes4,))
        self.gradcheck(partial(apply_boxes_method, method="get_boxes_shape"), (t_boxes1,))
        self.gradcheck(lambda x: Boxes.from_tensor(x, mode="xyxy_plus").data, (t_boxes_xyxy,))
        self.gradcheck(lambda x: Boxes.from_tensor(x, mode="xywh").data, (t_boxes_xyxy1,))

    def test_compute_area(self):
        # Rectangle
        box_1 = [[0.0, 0.0], [100.0, 0.0], [100.0, 50.0], [0.0, 50.0]]
        # Trapezoid
        box_2 = [[0.0, 0.0], [60.0, 0.0], [40.0, 50.0], [20.0, 50.0]]
        # Parallelogram
        box_3 = [[0.0, 0.0], [100.0, 0.0], [120.0, 50.0], [20.0, 50.0]]
        # Random quadrilateral
        box_4 = [
            [50.0, 50.0],
            [150.0, 250.0],
            [0.0, 500.0],
            [27.0, 80],
        ]
        # Random quadrilateral
        box_5 = [
            [0.0, 0.0],
            [150.0, 0.0],
            [150.0, 150.0],
            [0.0, 0.5],
        ]
        # Rectangle with minus coordinates
        box_6 = [[-500.0, -500.0], [-300.0, -500.0], [-300.0, -300.0], [-500.0, -300.0]]

        expected_values = [5000.0, 2000.0, 5000.0, 31925.0, 11287.5, 40000.0]
        box_coordinates = torch.tensor([box_1, box_2, box_3, box_4, box_5, box_6])
        computed_areas = Boxes(box_coordinates).compute_area().tolist()
        computed_areas_w_batch = Boxes(box_coordinates.reshape(2, 3, 4, 2)).compute_area().tolist()
        flattened_computed_areas_w_batch = [area for batch in computed_areas_w_batch for area in batch]
        assert all(
            computed_area == expected_area for computed_area, expected_area in zip(computed_areas, expected_values)
        )
        assert all(
            computed_area == expected_area
            for computed_area, expected_area in zip(flattened_computed_areas_w_batch, expected_values)
        )


class TestTransformBoxes2D(BaseTester):
    def test_transform_boxes(self, device, dtype):
        # Define boxes in XYXY format for simplicity.
        boxes_xyxy = torch.tensor([[139.2640, 103.0150, 398.3120, 411.5225]], device=device, dtype=dtype)
        expected_boxes_xyxy = torch.tensor([[372.7360, 103.0150, 115.6880, 411.5225]], device=device, dtype=dtype)

        boxes = Boxes.from_tensor(boxes_xyxy)
        expected_boxes = Boxes.from_tensor(expected_boxes_xyxy, validate_boxes=False)

        trans_mat = torch.tensor([[[-1.0, 0.0, 512.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]], device=device, dtype=dtype)

        transformed_boxes = boxes.transform_boxes(trans_mat)
        self.assert_close(transformed_boxes.data, expected_boxes.data, atol=1e-4, rtol=1e-4)
        # inplace check
        assert transformed_boxes is not boxes

    def test_transform_boxes_(self, device, dtype):
        # Define boxes in XYXY format for simplicity.
        boxes_xyxy = torch.tensor([[139.2640, 103.0150, 398.3120, 411.5225]], device=device, dtype=dtype)
        expected_boxes_xyxy = torch.tensor([[372.7360, 103.0150, 115.6880, 411.5225]], device=device, dtype=dtype)

        boxes = Boxes.from_tensor(boxes_xyxy)
        expected_boxes = Boxes.from_tensor(expected_boxes_xyxy, validate_boxes=False)

        trans_mat = torch.tensor([[[-1.0, 0.0, 512.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]], device=device, dtype=dtype)

        transformed_boxes = boxes.transform_boxes_(trans_mat)
        self.assert_close(transformed_boxes.data, expected_boxes.data, atol=1e-4, rtol=1e-4)
        # inplace check
        assert transformed_boxes is boxes

    def test_transform_multiple_boxes(self, device, dtype):
        # Define boxes in XYXY format for simplicity.
        boxes_xyxy = torch.tensor(
            [
                [139.2640, 103.0150, 398.3120, 411.5225],
                [1.0240, 80.5547, 513.0000, 513.0000],
                [165.2053, 262.1440, 511.6347, 509.9280],
                [119.8080, 144.2067, 258.0240, 411.1292],
            ],
            device=device,
            dtype=dtype,
        ).repeat(2, 1, 1)  # 2 x 4 x 4 two images 4 boxes each

        expected_boxes_xyxy = torch.tensor(
            [
                [
                    [372.7360, 103.0150, 115.6880, 411.5225],
                    [510.9760, 80.5547, 1.0000, 513.0000],
                    [346.7947, 262.1440, 2.3653, 509.9280],
                    [392.1920, 144.2067, 255.9760, 411.1292],
                ],
                [
                    [139.2640, 103.0150, 398.3120, 411.5225],
                    [1.0240, 80.5547, 513.0000, 513.0000],
                    [165.2053, 262.1440, 511.6347, 509.9280],
                    [119.8080, 144.2067, 258.0240, 411.1292],
                ],
            ],
            device=device,
            dtype=dtype,
        )

        trans_mat = torch.tensor(
            [
                [[-1.0, 0.0, 512.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            ],
            device=device,
            dtype=dtype,
        )

        boxes = Boxes.from_tensor(boxes_xyxy)
        expected_boxes = Boxes.from_tensor(expected_boxes_xyxy, validate_boxes=False)

        out = boxes.transform_boxes(trans_mat)
        self.assert_close(out.data, expected_boxes.data, atol=1e-4, rtol=1e-4)

    def test_gradcheck(self, device):
        # Define boxes in XYXY format for simplicity.
        boxes_xyxy = torch.tensor(
            [
                [139.2640, 103.0150, 258.0480, 307.5075],
                [1.0240, 80.5547, 510.9760, 431.4453],
                [165.2053, 262.1440, 345.4293, 546.7840],
                [119.8080, 144.2067, 137.2160, 265.9225],
            ],
            device=device,
            dtype=torch.float64,
        )
        boxes = Boxes.from_tensor(boxes_xyxy)

        trans_mat = torch.tensor(
            [[[-1.0, 0.0, 512.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]], device=device, dtype=torch.float64
        )

        def _wrapper_transform_boxes(quadrilaterals, M):
            boxes = Boxes(quadrilaterals)
            boxes = boxes.transform_boxes(M)
            return boxes.data

        self.gradcheck(_wrapper_transform_boxes, (boxes.data, trans_mat))


class TestBbox3D(BaseTester):
    def test_smoke(self, device, dtype):
        def _create_tensor_box():
            # Sample two points of the 3d rect
            points = torch.rand(1, 6, device=device, dtype=dtype)

            # Fill according missing points
            tensor_boxes = torch.zeros(1, 8, 3, device=device, dtype=dtype)
            tensor_boxes[0, 0] = points[0][:3]
            tensor_boxes[0, 1, 0] = points[0][3]
            tensor_boxes[0, 1, 1] = points[0][1]
            tensor_boxes[0, 1, 2] = points[0][2]
            tensor_boxes[0, 2, 0] = points[0][3]
            tensor_boxes[0, 2, 1] = points[0][4]
            tensor_boxes[0, 2, 2] = points[0][2]
            tensor_boxes[0, 3, 0] = points[0][0]
            tensor_boxes[0, 3, 1] = points[0][4]
            tensor_boxes[0, 3, 2] = points[0][2]
            tensor_boxes[0, 4, 0] = points[0][0]
            tensor_boxes[0, 4, 1] = points[0][1]
            tensor_boxes[0, 4, 2] = points[0][5]
            tensor_boxes[0, 5, 0] = points[0][3]
            tensor_boxes[0, 5, 1] = points[0][1]
            tensor_boxes[0, 5, 2] = points[0][5]
            tensor_boxes[0, 6] = points[0][3:]
            tensor_boxes[0, 7, 0] = points[0][0]
            tensor_boxes[0, 7, 1] = points[0][4]
            tensor_boxes[0, 7, 2] = points[0][5]
            return tensor_boxes

        # Validate
        assert Boxes3D(_create_tensor_box())  # Validate 1 box

        # 2 boxes without batching (N, 8, 3) where N=2
        two_boxes = torch.cat([_create_tensor_box(), _create_tensor_box()])
        assert Boxes3D(two_boxes)

        # 2 boxes in batch (B, 1, 8, 3) where B=2
        batched_bbox = torch.stack([_create_tensor_box(), _create_tensor_box()])
        assert Boxes3D(batched_bbox)

    def test_get_boxes_shape(self, device, dtype):
        box = Boxes3D(
            torch.tensor(
                [[[0, 1, 2], [0, 1, 32], [10, 21, 2], [0, 21, 2], [10, 1, 32], [10, 21, 32], [10, 1, 2], [0, 21, 32]]],
                device=device,
                dtype=dtype,
            )
        )  # 1x8x3
        t_boxes = torch.tensor(
            [
                [[0, 21, 32], [0, 1, 2], [10, 1, 2], [0, 21, 2], [0, 1, 32], [10, 21, 2], [10, 1, 32], [10, 21, 32]],
                [[3, 4, 5], [3, 4, 65], [43, 54, 5], [3, 54, 5], [43, 4, 5], [43, 4, 65], [43, 54, 65], [3, 54, 65]],
            ],
            device=device,
            dtype=dtype,
        )  # 2x8x3
        boxes = Boxes3D(t_boxes)
        boxes_batch = Boxes3D(t_boxes[None])  # (1, 2, 8, 3)

        # Single box
        d, h, w = box.get_boxes_shape()
        assert (d.item(), h.item(), w.item()) == (31.0, 21.0, 11.0)

        # Boxes
        d, h, w = boxes.get_boxes_shape()
        assert h.ndim == 1
        assert w.ndim == 1
        assert len(d) == 2
        assert len(h) == 2
        assert len(w) == 2
        self.assert_close(d, torch.as_tensor([31.0, 61.0], device=device, dtype=dtype))
        self.assert_close(h, torch.as_tensor([21.0, 51.0], device=device, dtype=dtype))
        self.assert_close(w, torch.as_tensor([11.0, 41.0], device=device, dtype=dtype))

        # Box batch
        d, h, w = boxes_batch.get_boxes_shape()
        assert h.ndim == 2
        assert w.ndim == 2
        assert h.shape == (1, 2)
        assert w.shape == (1, 2)
        self.assert_close(d, torch.as_tensor([[31.0, 61.0]], device=device, dtype=dtype))
        self.assert_close(h, torch.as_tensor([[21.0, 51.0]], device=device, dtype=dtype))
        self.assert_close(w, torch.as_tensor([[11.0, 41.0]], device=device, dtype=dtype))

    def test_get_boxes_shape_batch(self, device, dtype):
        t_box1 = torch.tensor(
            [[[0, 1, 2], [0, 1, 32], [10, 21, 2], [0, 21, 2], [10, 1, 32], [10, 21, 32], [10, 1, 2], [0, 21, 32]]],
            device=device,
            dtype=dtype,
        )
        t_box2 = torch.tensor(
            [[[3, 4, 5], [3, 4, 65], [43, 54, 5], [3, 54, 5], [43, 4, 5], [43, 4, 65], [43, 54, 65], [3, 54, 65]]],
            device=device,
            dtype=dtype,
        )
        batched_boxes = Boxes3D(torch.stack([t_box1, t_box2]))

        d, h, w = batched_boxes.get_boxes_shape()
        assert d.ndim == 2
        assert h.ndim == 2
        assert w.ndim == 2
        assert d.shape == (2, 1)
        assert h.shape == (2, 1)
        assert w.shape == (2, 1)
        self.assert_close(d, torch.as_tensor([[31.0], [61.0]], device=device, dtype=dtype))
        self.assert_close(h, torch.as_tensor([[21.0], [51.0]], device=device, dtype=dtype))
        self.assert_close(w, torch.as_tensor([[11.0], [41.0]], device=device, dtype=dtype))

    @pytest.mark.parametrize("shape", [(1, 6), (1, 1, 6)])
    def test_from_tensor(self, shape, device, dtype):
        box_xyzxyz = torch.as_tensor([[1, 2, 3, 4, 5, 6]], device=device, dtype=dtype).view(*shape)
        box_xyzxyz_plus = torch.as_tensor([[1, 2, 3, 3, 4, 5]], device=device, dtype=dtype).view(*shape)
        box_xyzwhd = torch.as_tensor([[1, 2, 3, 3, 3, 3]], device=device, dtype=dtype).view(*shape)

        expected_box = torch.as_tensor(
            [[[1, 2, 3], [3, 2, 3], [3, 4, 3], [1, 4, 3], [1, 2, 5], [3, 2, 5], [3, 4, 5], [1, 4, 5]]],  # Front  # Back
            device=device,
            dtype=dtype,
        ).view(*shape[:-1], 8, 3)

        kornia_xyzxyz = Boxes3D.from_tensor(box_xyzxyz, mode="xyzxyz").data
        kornia_xyzxyz_plus = Boxes3D.from_tensor(box_xyzxyz_plus, mode="xyzxyz_plus").data
        kornia_xyzwhd = Boxes3D.from_tensor(box_xyzwhd, mode="xyzwhd").data

        assert kornia_xyzxyz.shape == expected_box.shape
        self.assert_close(kornia_xyzxyz, expected_box)

        assert kornia_xyzxyz_plus.shape == expected_box.shape
        self.assert_close(kornia_xyzxyz_plus, expected_box)

        assert kornia_xyzwhd.shape == expected_box.shape
        self.assert_close(kornia_xyzwhd, expected_box)

    @pytest.mark.parametrize("shape", [(1, 6), (1, 1, 6)])
    def test_from_invalid_tensor(self, shape, device, dtype):
        box_xyzxyz = torch.as_tensor([[1, 2, 3, 4, -5, 6]], device=device, dtype=dtype).view(*shape)
        box_xyzxyz_plus = torch.as_tensor([[1, 2, 3, 0, 6, 4]], device=device, dtype=dtype).view(*shape)

        try:
            Boxes3D.from_tensor(box_xyzxyz, mode="xyzxyz")
            raise AssertionError("Boxes3D.from_tensor should have raised any exception")
        except ValueError:
            pass

        try:
            Boxes3D.from_tensor(box_xyzxyz_plus, mode="xyzxyz_plus")
            raise AssertionError("Boxes3D.from_tensor should have raised any exception")
        except ValueError:
            pass

    @pytest.mark.parametrize("shape", [(1, 6), (1, 1, 6)])
    def test_boxes_to_tensor(self, shape, device, dtype):
        # Hexahedron with randomized vertices to reflect possible transforms.
        box = Boxes3D(
            torch.as_tensor(
                [[[2, 2, 1], [1, 2, 1], [2, 3, 2], [1, 3, 2], [2, 2, 2], [1, 3, 1], [2, 3, 1], [1, 2, 2]]],
                device=device,
                dtype=dtype,
            ).view(*shape[:-1], 8, 3)
        )

        expected_box_xyzxyz = torch.as_tensor([[1, 2, 1, 3, 4, 3]], device=device, dtype=dtype).view(*shape)
        expected_box_xyzxyz_plus = torch.as_tensor([[1, 2, 1, 2, 3, 2]], device=device, dtype=dtype).view(*shape)
        expected_box_xyzwhd = torch.as_tensor([[1, 2, 1, 2, 2, 2]], device=device, dtype=dtype).view(*shape)
        expected_vertices = torch.as_tensor(
            [[[1, 2, 1], [3, 2, 1], [3, 4, 1], [1, 4, 1], [1, 2, 3], [3, 2, 3], [3, 4, 3], [1, 4, 3]]],  # Front  # Back
            device=device,
            dtype=dtype,
        ).view(*shape[:-1], 8, 3)
        expected_vertices_plus = torch.as_tensor(
            [[[1, 2, 1], [2, 2, 1], [2, 3, 1], [1, 3, 1], [1, 2, 2], [2, 2, 2], [2, 3, 2], [1, 3, 2]]],  # Front  # Back
            device=device,
            dtype=dtype,
        ).view(*shape[:-1], 8, 3)

        kornia_xyzxyz = box.to_tensor(mode="xyzxyz")
        kornia_xyzxyz_plus = box.to_tensor(mode="xyzxyz_plus")
        kornia_xyzwhd = box.to_tensor(mode="xyzwhd")
        kornia_vertices = box.to_tensor(mode="vertices")
        kornia_vertices_plus = box.to_tensor(mode="vertices_plus")

        assert kornia_xyzxyz.shape == expected_box_xyzxyz.shape
        self.assert_close(kornia_xyzxyz, expected_box_xyzxyz)

        assert kornia_xyzxyz_plus.shape == expected_box_xyzxyz_plus.shape
        self.assert_close(kornia_xyzxyz_plus, expected_box_xyzxyz_plus)

        assert kornia_xyzwhd.shape == expected_box_xyzwhd.shape
        self.assert_close(kornia_xyzwhd, expected_box_xyzwhd)

        assert kornia_vertices.shape == expected_vertices.shape
        self.assert_close(kornia_vertices, expected_vertices)

        assert kornia_vertices_plus.shape == expected_vertices_plus.shape
        self.assert_close(kornia_vertices_plus, expected_vertices_plus)

    def test_bbox_to_mask(self, device, dtype):
        t_box1 = torch.tensor(
            [
                [
                    [1.0, 1.0, 1.0],
                    [3.0, 1.0, 1.0],
                    [3.0, 2.0, 1.0],
                    [1.0, 2.0, 1.0],  # Front
                    [1.0, 1.0, 2.0],
                    [3.0, 1.0, 2.0],
                    [3.0, 2.0, 2.0],
                    [1.0, 2.0, 2.0],  # Back
                ]
            ],
            device=device,
            dtype=dtype,
        )  # (1, 8, 3)
        t_box2 = torch.tensor(
            [
                [
                    [2.0, 2.0, 1.0],
                    [4.0, 2.0, 1.0],
                    [4.0, 5.0, 1.0],
                    [4.0, 2.0, 1.0],  # Front
                    [2.0, 2.0, 1.0],
                    [4.0, 2.0, 1.0],
                    [4.0, 5.0, 1.0],
                    [4.0, 5.0, 1.0],  # Back
                ]
            ],
            device=device,
            dtype=dtype,
        )  # (1, 8, 3)

        box1, box2 = Boxes3D(t_box1), Boxes3D(t_box2)
        two_boxes = Boxes3D(torch.cat([t_box1, t_box2]))  # (2, 8, 3)
        batched_boxes = Boxes3D(torch.stack([t_box1, t_box2]))  # (2, 1, 8, 3)

        depth, height, width = 3, 7, 5

        expected_mask1 = torch.tensor(
            [
                [
                    [  # Depth 0
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                    ],
                    [  # Depth 1
                        [0, 0, 0, 0, 0],
                        [0, 1, 1, 1, 0],
                        [0, 1, 1, 1, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                    ],
                    [  # Depth 2
                        [0, 0, 0, 0, 0],
                        [0, 1, 1, 1, 0],
                        [0, 1, 1, 1, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                    ],
                ]
            ],
            device=device,
            dtype=dtype,
        )

        expected_mask2 = torch.tensor(
            [
                [
                    [  # Depth 0
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                    ],
                    [  # Depth 1
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 1, 1, 1],
                        [0, 0, 1, 1, 1],
                        [0, 0, 1, 1, 1],
                        [0, 0, 1, 1, 1],
                        [0, 0, 0, 0, 0],
                    ],
                    [  # Depth 2
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                    ],
                ]
            ],
            device=device,
            dtype=dtype,
        )
        expected_two_masks = torch.cat([expected_mask1, expected_mask2])
        expected_batched_masks = torch.stack([expected_mask1, expected_mask2])

        mask1 = box1.to_mask(depth, height, width)
        mask2 = box2.to_mask(depth, height, width)
        two_masks = two_boxes.to_mask(depth, height, width)
        batched_masks = batched_boxes.to_mask(depth, height, width)

        assert mask1.shape == expected_mask1.shape
        self.assert_close(mask1, expected_mask1)

        assert mask2.shape == expected_mask2.shape
        self.assert_close(mask2, expected_mask2)

        assert two_masks.shape == expected_two_masks.shape
        self.assert_close(two_masks, expected_two_masks)

        assert batched_masks.shape == expected_batched_masks.shape
        self.assert_close(batched_masks, expected_batched_masks)

    def test_to(self, device, dtype):
        boxes = Boxes3D.from_tensor(torch.as_tensor([[1, 2, 3, 4, 5, 6]], device="cpu", dtype=torch.float32))
        assert boxes.to(device=device).data.device == device
        assert boxes.to(dtype=dtype).data.dtype == dtype

        boxes_moved = boxes.to(device, dtype)
        assert boxes_moved is boxes  # to is an inplace op.
        assert boxes_moved.data.device == device, boxes_moved.data.dtype == dtype

    def test_gradcheck(self, device):
        # Uncomment when enabling gradient checks
        # def apply_boxes_method(tensor: torch.Tensor, method: str, **kwargs):
        #     boxes = Boxes3D(tensor)
        #     result = getattr(boxes, method)(**kwargs)
        #     return result.data if isinstance(result, Boxes3D) else result

        # t_boxes1 = torch.tensor(
        #     [
        #         [
        #             [0.0, 1.0, 2.0],
        #             [10, 1, 2],
        #             [10, 21, 2],
        #             [0, 21, 2],
        #             [0, 1, 32],
        #             [10, 1, 32],
        #             [10, 21, 32],
        #             [0, 21, 32],
        #         ]
        #     ],
        #     device=device,
        #     dtype=torch.float64,
        # )

        # Uncomment when enabling gradient checks
        # t_boxes2 = tensor_to_gradcheck_var(t_boxes1.detach().clone())
        # t_boxes3 = tensor_to_gradcheck_var(t_boxes1.detach().clone())
        # t_boxes4 = tensor_to_gradcheck_var(t_boxes1.detach().clone())
        t_boxes_xyzxyz = torch.tensor([[1.0, 3.0, 8.0, 5.0, 6.0, 12.0]], device=device, dtype=torch.float64)
        t_boxes_xyzxyz1 = t_boxes_xyzxyz.detach().clone()

        # Gradient checks for Boxes3D.to_tensor (and Boxes3D.get_boxes_shape) are disable since the is a bug
        # in their gradient. See https://github.com/kornia/kornia/issues/1396.
        # assert gradcheck(partial(apply_boxes_method, method='to_tensor'), (t_boxes2,), raise_exception=True)
        # assert gradcheck(
        #     partial(apply_boxes_method, method='to_tensor', mode='xyzxyz_plus'), (t_boxes3,), raise_exception=True
        # )
        # assert gradcheck(
        #     partial(apply_boxes_method, method='to_tensor', mode='vertices_plus'), (t_boxes4,), raise_exception=True
        # )
        # assert gradcheck(partial(apply_boxes_method, method='get_boxes_shape'), (t_boxes1,), raise_exception=True)
        self.gradcheck(lambda x: Boxes3D.from_tensor(x, mode="xyzxyz_plus").data, (t_boxes_xyzxyz,))
        self.gradcheck(lambda x: Boxes3D.from_tensor(x, mode="xyzwhd").data, (t_boxes_xyzxyz1,))


class TestTransformBoxes3D(BaseTester):
    def test_transform_boxes(self, device, dtype):
        # Define boxes in XYZXYZ format for simplicity.
        boxes_xyzxyz = torch.tensor(
            [[139.2640, 103.0150, 283.162, 398.3120, 411.5225, 454.185]], device=device, dtype=dtype
        )
        expected_boxes_xyzxyz = torch.tensor(
            [[372.7360, 103.0150, 567.324, 115.6880, 411.5225, 908.37]], device=device, dtype=dtype
        )

        boxes = Boxes3D.from_tensor(boxes_xyzxyz)
        expected_boxes = Boxes3D.from_tensor(expected_boxes_xyzxyz, validate_boxes=False)

        trans_mat = torch.tensor(
            [[[-1.0, 0.0, 0.0, 512.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 2.0, 1.0], [0.0, 0.0, 0.0, 1.0]]],
            device=device,
            dtype=dtype,
        )

        transformed_boxes = boxes.transform_boxes(trans_mat)
        self.assert_close(transformed_boxes.data, expected_boxes.data, atol=1e-4, rtol=1e-4)
        # inplace check
        assert transformed_boxes is not boxes

    def test_transform_boxes_(self, device, dtype):
        # Define boxes in XYZXYZ format for simplicity.
        boxes_xyzxyz = torch.tensor(
            [[139.2640, 103.0150, 283.162, 398.3120, 411.5225, 454.185]], device=device, dtype=dtype
        )
        expected_boxes_xyzxyz = torch.tensor(
            [[372.7360, 103.0150, 567.324, 115.6880, 411.5225, 908.37]], device=device, dtype=dtype
        )

        boxes = Boxes3D.from_tensor(boxes_xyzxyz)
        expected_boxes = Boxes3D.from_tensor(expected_boxes_xyzxyz, validate_boxes=False)

        trans_mat = torch.tensor(
            [[[-1.0, 0.0, 0.0, 512.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 2.0, 1.0], [0.0, 0.0, 0.0, 1.0]]],
            device=device,
            dtype=dtype,
        )

        transformed_boxes = boxes.transform_boxes_(trans_mat)
        self.assert_close(transformed_boxes.data, expected_boxes.data, atol=1e-4, rtol=1e-4)
        # inplace check
        assert transformed_boxes is boxes

    def test_transform_multiple_boxes(self, device, dtype):
        # Define boxes in XYZXYZ format for simplicity.
        boxes_xyzxyz = torch.tensor(
            [
                [139.2640, 103.0150, 283.162, 398.3120, 411.5225, 454.185],
                [1.0240, 80.5547, 469.50, 513.0000, 513.0000, 513.0],
                [165.2053, 262.1440, 42.98, 511.6347, 509.9280, 785.443],
                [119.8080, 144.2067, 234.21, 258.0240, 411.1292, 387.14],
            ],
            device=device,
            dtype=dtype,
        ).repeat(2, 1, 1)  # 2 x 4 x 4 two images 4 boxes each

        expected_boxes_xyzxyz = torch.tensor(
            [
                [
                    [372.7360, 103.0150, 567.324, 115.6880, 411.5225, 908.37],
                    [510.9760, 80.5547, 940.0, 1.0000, 513.0000, 1026.0],
                    [346.7947, 262.1440, 86.96, 2.3653, 509.9280, 1570.886],
                    [392.1920, 144.2067, 469.42, 255.9760, 411.1292, 774.28],
                ],
                [
                    [139.2640, 103.0150, 283.162, 398.3120, 411.5225, 454.185],
                    [1.0240, 80.5547, 469.50, 513.0000, 513.0000, 513.0],
                    [165.2053, 262.1440, 42.98, 511.6347, 509.9280, 785.443],
                    [119.8080, 144.2067, 234.21, 258.0240, 411.1292, 387.14],
                ],
            ],
            device=device,
            dtype=dtype,
        )

        trans_mat = torch.tensor(
            [
                [[-1.0, 0.0, 0.0, 512.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 2.0, 1.0], [0.0, 0.0, 0.0, 1.0]],
                [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]],
            ],
            device=device,
            dtype=dtype,
        )

        boxes = Boxes3D.from_tensor(boxes_xyzxyz)
        expected_boxes = Boxes3D.from_tensor(expected_boxes_xyzxyz, validate_boxes=False)

        out = boxes.transform_boxes(trans_mat)
        self.assert_close(out.data, expected_boxes.data, atol=1e-4, rtol=1e-4)

    def test_gradcheck(self, device):
        # Define boxes in XYZXYZ format for simplicity.
        boxes_xyzxyz = torch.tensor(
            [
                [139.2640, 103.0150, 283.162, 397.3120, 410.5225, 453.185],
                [1.0240, 80.5547, 469.50, 512.0000, 512.0000, 512.0],
                [165.2053, 262.1440, 42.98, 510.6347, 508.9280, 784.443],
                [119.8080, 144.2067, 234.21, 257.0240, 410.1292, 386.14],
            ],
            device=device,
            dtype=torch.float64,
        )
        boxes = Boxes3D.from_tensor(boxes_xyzxyz)

        trans_mat = torch.tensor(
            [[[-1.0, 0.0, 0.0, 512.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 2.0, 1.0], [0.0, 0.0, 0.0, 1.0]]],
            device=device,
            dtype=torch.float64,
        )

        def _wrapper_transform_boxes(hexahedrons, M):
            boxes = Boxes3D(hexahedrons)
            boxes = boxes.transform_boxes(M)
            return boxes.data

        self.gradcheck(_wrapper_transform_boxes, (boxes.data, trans_mat))
