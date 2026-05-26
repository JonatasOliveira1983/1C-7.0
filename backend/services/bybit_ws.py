# -*- coding: utf-8 -*-
# Legacy Bridge for OKX Public WebSocket transition.
# Prevents breaking hundreds of imports in legacy agents.
from services.okx_ws_public import okx_ws_public_service as bybit_ws_service
