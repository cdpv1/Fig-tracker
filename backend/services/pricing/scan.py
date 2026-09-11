from backend.database.prices import add_price_observation
from backend.services.pricing.hlj import find_hlj_product
from backend.database.figures import get_figures


def scan_hlj_price(figure):
    product = find_hlj_product(figure)

    if not product:
        return None

    add_price_observation(
        mfc_id=figure["mfc_id"],
        source=product["source"],
        price=product["price"],
        currency=product["currency"],
        item_condition=product["item_condition"],
        availability=product["availability"],
        listing_url=product["listing_url"],
    )

    return product

figures = get_figures()

for figure in figures:
    result = scan_hlj_price(figure)
    print(result)