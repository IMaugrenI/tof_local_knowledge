from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4


@dataclass
class CanonicalSegment:
    segment_id: str
    segment_kind: str
    ordinal: int
    page_no: int | None
    citation_label: str
    text: str


class ExtractionTranslator:
    """Übersetzt rohe Extraktionsblöcke in kanonische, zitierbare Segmente.

    Der Übersetzer ist bewusst klein und deterministisch gehalten.
    Er macht keine semantischen Behauptungen, sondern formt Rohblöcke in
    stabile Segmentobjekte um, die später such- und zitierbar sind.
    """

    def translate(self, document_id: str, raw_blocks: list[dict[str, Any]]) -> dict[str, Any]:
        segments: list[CanonicalSegment] = []
        warnings: list[str] = []

        for index, block in enumerate(raw_blocks, start=1):
            text = str(block.get('text', '')).strip()
            if not text:
                warnings.append(f'empty_block:{index}')
                continue

            page_no = block.get('page_no')
            segment_kind = str(block.get('kind', 'text_block'))
            citation = f'{document_id}#seg-{index}'
            segments.append(
                CanonicalSegment(
                    segment_id=str(uuid4()),
                    segment_kind=segment_kind,
                    ordinal=index,
                    page_no=page_no if isinstance(page_no, int) else None,
                    citation_label=citation,
                    text=text,
                )
            )

        read_status = 'unreadable'
        if segments:
            read_status = 'fully_read'
        elif raw_blocks:
            read_status = 'partially_read'

        return {
            'document_id': document_id,
            'segment_count': len(segments),
            'read_status': read_status,
            'warnings': warnings,
            'segments': [segment.__dict__ for segment in segments],
        }
