from mfc_api import MFCClient

def get_mfc_figure(mfc_id: int):
    with MFCClient() as client:
        item = client.get_item(mfc_id)
    return normalize_mfc_item(item)

def normalize_mfc_item(item):
    manufacturer = next(
        (
            company.name
            for company in item.companies
            if company.role == "Manufacturer"
        ),
        None
    )

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
        "release_date": release.date if release else None,
        "barcode": release.barcode if release else None,
        "msrp": release.price if release else None,
        "currency": release.currency if release else None,
        "rating": item.rating,
    }