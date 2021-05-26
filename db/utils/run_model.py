class RunModel:
    """Handler for a single instance of a model belonging to a run

    This module allows for holding of a model instance pre- or post-creation in
    the db, and therefore informs whether it requires creation.
    """

    def __init__(self, model_type, model_attributes, model_objects):
        self.model_type = model_type
        self.attrs = model_attributes
        self.model_objects = model_objects
        self.entry = None
        self.check_found_in_db()

    def check_found_in_db(self):
        """Query to check if there is a corresponding instance for this data"""
        entries = self.model_type.objects.filter(**self.attrs)
        if len(entries) == 1:
            entry = entries[0]
        elif len(entries) == 0:
            entry = False
        else:
            raise ValueError(f"Multiple of same object: {entries}")

        self.entry = entry
        return entry


class ManyRunModel:
    """Deals with situations where multiple RunModels are required eg for M2M

    The bulk update occurs using 'through' tables in such cases, so data for a
    set of these must be generated
    """

    def __init__(self, model_type, model_attributes_list, model_objects):
        self.model_type = model_type
        self.model_attributes_list = model_attributes_list
        self.model_objects = model_objects
        self.run_models = [
            RunModel(model_type, model_attributes, model_objects)
            for model_attributes in model_attributes_list
        ]

    def entry_list(self):
        return [run_model.entry for run_model in self.run_models]
