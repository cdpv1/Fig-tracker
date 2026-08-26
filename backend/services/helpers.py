from datetime import datetime

def normalize_mfc_item(item):
    manufacturer = next(
        (
            company.name
            for company in item.companies
            if (company.role or "").strip().casefold() == "manufacturer"
        ),
        None,
    )
    if manufacturer is None and item.companies:
        manufacturer = item.companies[0].name
    if manufacturer is None:
        manufacturer = "Unknown"

    origin = (
        item.origins[0].name
        if item.origins
        else None
    )

    release = (
        item.releases[0]
        if item.releases
        else None
    )
    return {
        "mfc_id": item.id,
        "name": item.name,
        "mfc_url": item.url,
        "picture_url": item.picture,
        "thumbnail_url": item.thumbnail,
        "category": item.category_name,
        "scale": item.scale,
        "height_mm": item.height_mm,
        "origin": origin,
        "manufacturer": manufacturer,
        "release_date": normalize_date(release.date) if release else None,
        "barcode": release.barcode if release else None,
        "msrp": release.price if release else None,
        "currency": release.currency if release else None,
        "rating": item.rating,
    }
    
def normalize_date(date_str):
    if date_str is None:
        return None
    formats = [
        ("%m/%d/%Y", "%Y-%m-%d"),
        ("%m/%Y", "%Y-%m"),
    ]

    for input_format, output_format in formats:
        try:
            parsed_date = datetime.strptime(date_str, input_format)
            return parsed_date.strftime(output_format)
        except ValueError:
            continue

    return None