#!/usr/bin/env bash

#
# Copyright 2016 The BigDL Authors.
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

# bigdl orca test only support pip, you have to install orca whl before running the script.
#. `dirname $0`/prepare_env.sh

set -ex

cd "`dirname $0`"
cd ../..

export PYSPARK_PYTHON=python
export PYSPARK_DRIVER_PYTHON=python

python_version=$(python --version | awk '{print$2}')
if [ $python_version == 3.7.10 ];then
  python -m pytest -v test/bigdl/orca/tfpark
  python -m pytest -v test/bigdl/orca/learn/spark --ignore=test/bigdl/orca/learn/spark/test_estimator_openvino.py

fi
python -m pytest -v test/bigdl/orca/learn/test_metrics.py
python -m pytest -v test/bigdl/orca/learn/test_utils.py
python -m pytest -v test/bigdl/orca/inference
