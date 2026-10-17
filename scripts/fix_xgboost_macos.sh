#!/bin/sh
# macOS only. xgboost's wheel needs libomp.dylib on its rpath; Homebrew's is not installed
# and we do not touch the system. PyTorch's wheel ships the same runtime, so point xgboost
# at it (venv-local change; re-signs the patched library ad hoc).
set -e
SP="$(./.venv/bin/python -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])')"
LIB="$SP/xgboost/lib/libxgboost.dylib"
[ -f "$SP/torch/lib/libomp.dylib" ] || { echo "torch libomp not found"; exit 1; }
otool -l "$LIB" | grep -q "torch/lib" || install_name_tool -add_rpath "@loader_path/../../torch/lib" "$LIB"
codesign --force -s - "$LIB" 2>/dev/null
./.venv/bin/python -c "import xgboost, numpy as np; xgboost.XGBClassifier(n_estimators=3).fit(np.random.rand(20,2), np.arange(20)%2); print('xgboost OK')"
