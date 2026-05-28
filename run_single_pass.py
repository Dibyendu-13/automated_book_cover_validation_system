from pathlib import Path

from bookleaf_validation.validators import CoverPayload, CoverValidator

p = Path("validation_book_covers/pass_book_cover.png")
result = CoverValidator().validate(
    CoverPayload(
        file_path=str(p),
        book_id="pass_book_cover",
        author_name="Unknown Author",
        elements=[],
    )
)
print(result.to_dict())

