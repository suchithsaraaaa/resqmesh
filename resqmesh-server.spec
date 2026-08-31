# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['backend/server_entrypoint.py'],
    pathex=['backend', 'backend/app'],
    binaries=[],
    datas=[],
    hiddenimports=['uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'app.sync.outbox_worker', 'app.sync.delta_sync', 'app.sync.attachment_sync', 'app.network.relay', 'app.services.incident_matcher', 'app.services.storage_service', 'app.api.attachments', 'app.ai.clustering', 'app.ai.similarity', 'app.ai.vector_store', 'app.ai.rag_pipeline', 'app.ai.llm_client'],
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
