from pydantic import BaseModel


class AudioPathRequest(BaseModel):
    audio_path: str
