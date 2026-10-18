import numpy as np

def cloud_percent(scl, data_mask) -> float | None:
    valid_mask = (data_mask == 1) & (scl != 0)
    count_valid_pixels = int(np.count_nonzero(valid_mask))

    cloud_classes = [8, 9, 10]
    cloud_mask = valid_mask & np.isin(scl, cloud_classes)
    cloud_pixels = int(np.count_nonzero(cloud_mask))

    return (100 * cloud_pixels / count_valid_pixels) if count_valid_pixels > 0 else None
