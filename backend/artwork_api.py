"""Immutable artwork catalog and versioned publication contract."""
import json
from fastapi import Depends, HTTPException, Request, Response
from pydantic import Field
from .models import StrictModel
from companion.artwork import MAX_B64, validate_artwork


class ArtworkSelection(StrictModel):
    artwork_id: str = Field(min_length=1, max_length=24, pattern=r'^[a-z0-9_-]+$')


def install_artwork_routes(app, db, admin, reader):
    @app.get('/api/v2/active', dependencies=[Depends(reader)])
    def active():
        return db.active_v2()

    @app.get('/api/v1/artworks', dependencies=[Depends(admin)])
    def list_artworks():
        return db.list_artworks()

    @app.post('/api/v1/artworks', status_code=201, dependencies=[Depends(admin)],
              openapi_extra={'requestBody': {'required': True, 'content': {'application/json': {'schema': {
                  'type': 'object', 'required': ['id', 'pack'], 'additionalProperties': False,
                  'properties': {'id': {'type': 'string', 'pattern': '^[a-z0-9_-]{1,24}$'},
                                 'pack': {'type': 'string', 'maxLength': MAX_B64, 'description': 'Base64 SVP1 binary pack'}}}}}}})
    async def create_artwork(request: Request):
        # Bound the actual streamed body, not just the Content-Length header.
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > MAX_B64 + 256:
                raise HTTPException(413, 'Artwork request too large')
            raw.extend(chunk)
        try:
            artwork = validate_artwork(json.loads(raw))
        except (ValueError, RecursionError):
            raise HTTPException(422, 'Invalid artwork pack') from None
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(db.create_artwork, artwork)

    @app.get('/api/v1/artworks/{artwork_id}', dependencies=[Depends(admin)])
    def get_artwork(artwork_id: str):
        return db.get_artwork(artwork_id)

    @app.delete('/api/v1/artworks/{artwork_id}', status_code=204, dependencies=[Depends(admin)])
    def delete_artwork(artwork_id: str):
        db.delete_artwork(artwork_id)
        return Response(status_code=204)

    @app.put('/api/v2/active/artwork', dependencies=[Depends(admin)])
    def publish_artwork(selection: ArtworkSelection):
        return db.activate_artwork(selection.artwork_id)
