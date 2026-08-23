from enum import Enum

class FigureStatus(Enum):
    OWNED = "owned"
    WISHLIST = "wishlist"
    FOR_SALE = "for_sale"
    FOR_TRADE = "for_trade"
    ORDERED = "ordered"