from mfc_api import MFCClient

def get_mfc_figure(mfc_id: int):
    with MFCClient() as client:
        item = client.get_item(mfc_id)
    return item