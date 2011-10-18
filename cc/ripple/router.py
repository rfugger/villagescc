"DB Router for Ripple models."

class RippleRouter(object):
    "Route Ripple models to separate DB."
    APPS = ('account', 'payment')
    DB_ALIAS = 'ripple'
    
    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.APPS:
            return self.DB_ALIAS
        return None
    
    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.APPS:
            return self.DB_ALIAS
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        if (obj1._meta.app_label in self.APPS and
            obj2._meta.app_label in self.APPS):
            return True
        return None
    
    def allow_syncdb(self, db, model):
        if db == self.DB_ALIAS:
            # Only put models from APPS into Ripple table (and south).
            return model._meta.app_label in self.APPS + ('south',)
        elif model._meta.app_label in self.APPS:
            # Don't put Ripple models anywhere else.
            return False
        return None
