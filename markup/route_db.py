class DemoRouter:
    """
    A router to control all database operations on models in the
    user application.
    """
    route_app_labels = {'cars', 'request'}

    def db_for_read(self, model, **hints):
        """
        Attempts to read user models go to shared_db.
        """
        if model._meta.app_label == 'cars':
            return 'shared_db'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write user models go to shared_db.
        """
        if model._meta.app_label == 'cars':
            return 'shared_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the user app is involved.
        """
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

        # if obj1._meta.app_label == 'cars' or \
        # obj2._meta.app_label == 'cars':
        #     return True
        # return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth app only appears in the 'shared_db'
        database.
        """
        if app_label == 'cars':
            return db == 'shared_db'
        return None
