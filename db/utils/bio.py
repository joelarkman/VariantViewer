class VariantManager:
    """Holds collected information about all variants in a MRA operation.

    Allows caching of information eg. sample, coordinates, of a variant whilst
    the initial model is saved to then come back and save/relate this info at a
    later time.
    """