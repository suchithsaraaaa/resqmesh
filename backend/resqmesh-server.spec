# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server_entrypoint.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'app.main', 'app.database', 'app.models', 'app.schemas', 'app.crypto.security', 'app.api.incidents', 'app.api.reports', 'app.api.messages', 'app.api.ai', 'app.api.node', 'app.services.node_manager', 'app.services.incident_matcher', 'app.network.discovery', 'app.network.transport', 'app.network.event_protocol', 'app.network.relay', 'app.network.router', 'app.network.protocol', 'app.sync.outbox_worker', 'app.sync.delta_sync', 'app.ai.similarity', 'app.ai.clustering', 'app.ai.vector_store', 'app.ai.rag_pipeline', 'app.ai.llm_client', 'app.ai.query_parser', 'cryptography', 'nacl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='resqmesh-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='resqmesh-server',
)
