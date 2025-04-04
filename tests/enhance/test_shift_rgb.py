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

import pytest
import torch

import kornia

from testing.base import BaseTester


class TestRGBShift(BaseTester):
    def test_rgb_shift_no_shift(self, device, dtype):
        r_shift, g_shift, b_shift = torch.Tensor([0]), torch.Tensor([0]), torch.Tensor([0])
        image = torch.rand(2, 3, 5, 5, device=device, dtype=dtype)
        expected = image
        shifted = kornia.enhance.shift_rgb(image, r_shift, g_shift, b_shift)

        self.assert_close(shifted, expected)

    def test_rgb_shift_all_zeros(self, device, dtype):
        r_shift, g_shift, b_shift = torch.Tensor([-0.1]), torch.Tensor([-0.1]), torch.Tensor([-0.1])
        image = torch.zeros(2, 3, 5, 5, device=device, dtype=dtype)
        expected = image
        shifted = kornia.enhance.shift_rgb(image, r_shift, g_shift, b_shift)

        self.assert_close(shifted, expected)

    def test_rgb_shift_all_ones(self, device, dtype):
        r_shift, g_shift, b_shift = torch.Tensor([1]), torch.Tensor([1]), torch.Tensor([1])
        image = torch.rand(2, 3, 5, 5, device=device, dtype=dtype)
        expected = torch.ones(2, 3, 5, 5, device=device, dtype=dtype)
        shifted = kornia.enhance.shift_rgb(image, r_shift, g_shift, b_shift)

        self.assert_close(shifted, expected)

    def test_rgb_shift_invalid_parameter_shape(self, device, dtype):
        r_shift, g_shift, b_shift = torch.Tensor([0.5]), torch.Tensor([0.5]), torch.Tensor([0.5])
        image = torch.randn(3, 3, device=device, dtype=dtype)
        with pytest.raises(TypeError):
            kornia.enhance.shift_rgb(image, r_shift, g_shift, b_shift)

    def test_rgb_shift_gradcheck(self, device):
        r_shift, g_shift, b_shift = torch.Tensor([0.4]), torch.Tensor([0.5]), torch.Tensor([0.2])
        image = torch.randn(2, 3, 5, 5, device=device, dtype=torch.float64)
        self.gradcheck(kornia.enhance.shift_rgb, (image, r_shift, g_shift, b_shift))

    def test_rgb_shift(self, device, dtype):
        r_shift, g_shift, b_shift = torch.Tensor([0.1]), torch.Tensor([0.3]), torch.Tensor([-0.3])
        image = torch.tensor(
            [[[[0.2, 0.0]], [[0.3, 0.5]], [[0.4, 0.7]]], [[[0.2, 0.7]], [[0.0, 0.8]], [[0.2, 0.3]]]],
            device=device,
            dtype=dtype,
        )
        shifted = kornia.enhance.shift_rgb(image, r_shift, g_shift, b_shift)
        expected = torch.tensor(
            [[[[0.3, 0.1]], [[0.6, 0.8]], [[0.1, 0.4]]], [[[0.3, 0.8]], [[0.3, 1.0]], [[0.0, 0.0]]]],
            device=device,
            dtype=dtype,
        )

        self.assert_close(shifted, expected)
